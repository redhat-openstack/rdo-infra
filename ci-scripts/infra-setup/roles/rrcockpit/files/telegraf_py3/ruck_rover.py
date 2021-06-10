#!/usr/bin/env python


import os
import re
from datetime import datetime

import click
import dlrnapi_client
import requests
import yaml
from dlrnapi_client.rest import ApiException
from rich.console import Console
from rich.table import Table

console = Console()


def date_diff_in_seconds(dt2, dt1):
    timedelta = dt2 - dt1

    return timedelta.days * 24 * 3600 + timedelta.seconds


def dhms_from_seconds(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return (hours, minutes, seconds)


def strip_date_time_from_string(input_string):
    regex_object = re.compile(r'[\d*-]*\d* [\d*:]*')

    return regex_object.search(input_string).group()


def convert_string_date_object(date_string):
    return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')


def download_file(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open("/tmp/job-output.txt", "wb") as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)


def delete_file(path):
    os.remove(path)


def find_job_run_time(url):
    try:
        download_file(url + "/job-output.txt")
    except requests.exceptions.RequestException:
        return "N/A"
    with open("/tmp/job-output.txt", "r") as file:
        first_line = file.readline()
        for last_line in file:
            pass
    start_time = strip_date_time_from_string(first_line)
    start_time_ob = convert_string_date_object(start_time)
    end_time = strip_date_time_from_string(last_line)
    end_time_ob = convert_string_date_object(end_time)

    hours, minutes, seconds = dhms_from_seconds(
        date_diff_in_seconds(end_time_ob, start_time_ob))
    delete_file("/tmp/job-output.txt")
    return f"{hours} hr {minutes} mins {seconds} secs"


def web_scrap(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    except requests.exceptions.RequestException as error:
        raise SystemExit(error)

    return response.text


def url_response_in_yaml(url):
    text_response = web_scrap(url)
    processed_data = yaml.safe_load(text_response)

    return processed_data


def gather_basic_info_from_criteria(url):
    criteria_content = url_response_in_yaml(url)
    api_url = criteria_content['api_url']
    base_url = criteria_content['base_url']

    return api_url, base_url


def find_jobs_in_integration_criteria(url):
    criteria_content = url_response_in_yaml(url)

    return criteria_content['promotions']['current-tripleo']['criteria']


def find_jobs_in_component_criteria(url, component):
    criteria_content = url_response_in_yaml(url)

    return criteria_content['promoted-components'][component]


def fetch_hashes_from_commit_yaml(url):
    """
    This function finds commit hash, distro hash, extended_hash from commit.yaml
    :param url for commit.yaml
    :returns strings for commit_hash, distro_hash, extended_hash
    """
    commit_yaml_content = url_response_in_yaml(url)
    commit_hash = commit_yaml_content['commits'][0]['commit_hash']
    distro_hash = commit_yaml_content['commits'][0]['distro_hash']
    extended_hash = commit_yaml_content['commits'][0]['extended_hash']

    return commit_hash, distro_hash, extended_hash


def find_results_from_dlrn_agg(api_url, test_hash):
    api_client = dlrnapi_client.ApiClient(host=api_url)
    api_instance = dlrnapi_client.DefaultApi(api_client)
    params = dlrnapi_client.AggQuery(aggregate_hash=test_hash)
    api_response = api_instance.api_agg_status_get(params=params)

    return api_response


def find_results_from_dlrn_repo_status(api_url, commit_hash,
                                       distro_hash, extended_hash):
    """ This function returns api_response from dlrn for a particular
        commit_hash, distro_hash, extended_hash.
        https://github.com/softwarefactory-project/dlrnapi_client/blob/master/
        docs/DefaultApi.md#api_repo_status_get

        :param api_url: the dlrn api endpoint for a particular release
        :param commit_hash: For a particular repo, commit.yaml contains this
         info.
        :param distro_hash: For a particular repo, commit.yaml contains this
         info.
        :param extended_hash: For a particular repo, commit.yaml contains this
         info.
        :return api_response: from dlrnapi server containing result of
         passing/failing jobs
    """
    if extended_hash == "None":
        extended_hash = None
    api_client = dlrnapi_client.ApiClient(host=api_url)
    api_instance = dlrnapi_client.DefaultApi(api_client)
    params = dlrnapi_client.Params2(commit_hash=commit_hash,
                                    distro_hash=distro_hash,
                                    extended_hash=extended_hash)
    try:
        api_response = api_instance.api_repo_status_get(params=params)
    except ApiException as err:
        print("Exception when calling DefaultApi->api_repo_status_get:"
              " %s\n" % err)
    return api_response


def conclude_results_from_dlrn(api_response):
    passed_jobs = set()
    all_jobs_result_available = set()
    for job in api_response:
        if job.job_id.startswith("periodic"):
            all_jobs_result_available.add(job.job_id)
            if job.success:
                passed_jobs.add(job.job_id)

    failed_jobs = all_jobs_result_available.difference(passed_jobs)

    return all_jobs_result_available, passed_jobs, failed_jobs


def latest_failing_job_results_url(api_response, failed_jobs):
    logs_failing_job = {}
    for failed_job in failed_jobs:
        latest_log = {}
        for job in api_response:
            if job.job_id == failed_job:
                latest_log[job.timestamp] = job.url
        logs_failing_job[failed_job] = latest_log[max(latest_log.keys())]

    return logs_failing_job


def print_a_set_in_table(input_set, header="Job name"):
    table = Table(show_header=True, header_style="bold")
    table.add_column(header, style="dim", width=80)
    for job in input_set:
        table.add_row(job)
    console.print(table)


def influxdb(jobs_result):
    # https://docs.influxdata.com/influxdb/v2.0/reference/syntax/line-protocol/
    # jobs_result = the measurement
    # job_type is a tag, note the space
    # rest of the values are fields in a row of data
    results_influxdb_line = ('jobs_result,'
                             'job_type={job_type},'
                             'job_name={job},'
                             'release={release} '
                             'name="{promote_name}",'
                             'test_hash="{test_hash}",'
                             'criteria="{criteria}",'
                             'status="{status}",'
                             'logs="{logs}",'
                             'duration="{duration}",'
                             'component="{component}"')

    if jobs_result['component'] is None:
        jobs_result['job_type'] = "integration"
    else:
        jobs_result['job_type'] = "component"
    return results_influxdb_line.format(**jobs_result)


def track_integration_promotion(release='master',
                                promotion="current-tripleo",
                                influx=False):
    if release == 'master':
        promoter_url = 'http://10.0.148.74/config/CentOS-8/'
    else:
        promoter_url = 'http://38.102.83.109/config/CentOS-8/'
    url = promoter_url + release + '.yaml'
    api_url, base_url = gather_basic_info_from_criteria(url)
    md5sum_url = base_url + 'tripleo-ci-testing/delorean.repo.md5'
    test_hash = web_scrap(md5sum_url)
    api_response = find_results_from_dlrn_agg(api_url, test_hash)
    (all_jobs_result_available,
     passed_jobs, failed_jobs) = conclude_results_from_dlrn(api_response)
    jobs_in_criteria = set(find_jobs_in_integration_criteria(url))
    jobs_which_need_pass_to_promote = jobs_in_criteria.difference(passed_jobs)
    jobs_with_no_result = jobs_in_criteria.difference(all_jobs_result_available)
    all_jobs = all_jobs_result_available.union(jobs_with_no_result)
    if influx:
        failing_log_urls = latest_failing_job_results_url(
            api_response, all_jobs_result_available)
        for job in all_jobs:
            if job in passed_jobs:
                status = 'passed'
            elif job in failed_jobs:
                status = 'failed'
            else:
                status = 'pending'
            jobs_result = {}
            jobs_result['release'] = release
            jobs_result['promote_name'] = promotion
            jobs_result['job'] = job
            jobs_result['test_hash'] = test_hash
            jobs_result['component'] = None
            jobs_result['criteria'] = job in jobs_in_criteria
            jobs_result['status'] = status
            jobs_result['logs'] = failing_log_urls.get(job, "N/A")
            jobs_result['duration'] = find_job_run_time(
                failing_log_urls.get(job, "N/A"))
            print(influxdb(jobs_result))

    else:
        console.print(f"Hash under test: {test_hash}")
        print_a_set_in_table(passed_jobs, "Jobs which passed:")
        print_a_set_in_table(failed_jobs, "Jobs which failed:")
        print_a_set_in_table(jobs_with_no_result,
                             "Jobs whose results are awaited")
        print_a_set_in_table(jobs_which_need_pass_to_promote,
                             "Jobs which are in promotion criteria and need "
                             "pass to promote the Hash: ")
        console.print("Logs of jobs which are failing:-")
        failing_log_urls = latest_failing_job_results_url(api_response,
                                                          failed_jobs)
        for value in failing_log_urls.values():
            console.print(value)


def track_component_promotion(release, test_component,
                              promotion="promoted-components",
                              influx=False):
    """ Find the failing jobs which are blocking promotion of a component.
    :param release: The OpenStack release e.g. wallaby
    :param component:
    """

    if test_component == "all":
        all_components = ["baremetal", "cinder", "clients", "cloudops",
                          "common", "compute", "glance", "manila",
                          "network", "octavia", "security", "swift",
                          "tempest", "tripleo", "ui", "validation"]
    else:
        all_components = [test_component]

    git_url = ('https://raw.githubusercontent.com/rdo-infra/ci-config/master/'
               'ci-scripts/dlrnapi_promoter/config/CentOS-8/component/')
    url = git_url + release + '.yaml'
    api_url, base_url = gather_basic_info_from_criteria(url)
    for component in all_components:
        commit_url = '{}component/{}/component-ci-testing/commit.yaml'.format(
                          base_url, component)
        commit_hash, distro_hash, extended_hash = fetch_hashes_from_commit_yaml(
                                                    commit_url)
        api_response = find_results_from_dlrn_repo_status(api_url,
                                                          commit_hash,
                                                          distro_hash,
                                                          extended_hash)
        (all_jobs_result_available,
         passed_jobs, failed_jobs) = conclude_results_from_dlrn(api_response)
        if 'consistent' in all_jobs_result_available:
            all_jobs_result_available.remove('consistent')
        if 'consistent' in passed_jobs:
            passed_jobs.remove('consistent')
        if 'consistent' in failed_jobs:
            failed_jobs.remove('consistent')
        jobs_in_criteria = set(find_jobs_in_component_criteria(url, component))

        jobs_which_need_pass_to_promote = jobs_in_criteria.difference(
                                            passed_jobs)
        jobs_with_no_result = jobs_in_criteria.difference(
            all_jobs_result_available)
        all_jobs = all_jobs_result_available.union(jobs_with_no_result)
        if influx:
            failing_log_urls = latest_failing_job_results_url(
                api_response, all_jobs_result_available)
            for job in all_jobs:
                if job in passed_jobs:
                    status = 'passed'
                elif job in failed_jobs:
                    status = 'failed'
                else:
                    status = 'pending'
                jobs_result = {}
                jobs_result['release'] = release
                jobs_result['promote_name'] = promotion
                jobs_result['job'] = job
                jobs_result['test_hash'] = commit_hash + '_' + distro_hash[0:8]
                jobs_result['component'] = component
                jobs_result['criteria'] = job in jobs_in_criteria
                jobs_result['status'] = status
                jobs_result['logs'] = failing_log_urls.get(
                                         job, "N/A")
                jobs_result['duration'] = find_job_run_time(
                    failing_log_urls.get(job, "N/A"))
                print(influxdb(jobs_result))
        else:
            failing_log_urls = latest_failing_job_results_url(api_response,
                                                              failed_jobs)
            header = ("{} component jobs which need pass to promote "
                      "the hash: ").format(component)
            if failed_jobs:
                component_status = "Red"
            elif not jobs_which_need_pass_to_promote:
                component_status = "Green"
            else:
                component_status = "Yellow"
            console.print(f"{component} component, status={component_status}")
            print_a_set_in_table(passed_jobs, "Jobs which passed:")
            if component_status != "Green":
                print_a_set_in_table(failed_jobs, "Jobs which failed:")
                print_a_set_in_table(jobs_with_no_result,
                                     "Jobs whose results are awaited")
                print_a_set_in_table(jobs_which_need_pass_to_promote, header)
                if component_status == "Red":
                    console.print("Logs of failing jobs:")
                    for value in failing_log_urls.values():
                        console.print(value)
            print('\n')


@ click.command()
@ click.option("--release", default='master',
               type=click.Choice(['master', 'wallaby', 'victoria', 'ussuri',
                                  'train', 'osp17', 'osp16-2']))
@ click.option("--component",
               type=click.Choice(["all", "baremetal", "cinder", "clients",
                                  "cloudops", "common", "compute",
                                  "glance", "manila", "network", "octavia",
                                  "security", "swift", "tempest", "tripleo",
                                  "ui", "validation"]))
@ click.option("--influx", is_flag=True, default=False)
def main(release='master', influx=False, component=None):
    if component:
        track_component_promotion(release=release,
                                  test_component=component,
                                  promotion="promoted-components",
                                  influx=influx)
    else:
        track_integration_promotion(release=release,
                                    promotion="current-tripleo",
                                    influx=influx)


if __name__ == '__main__':
    main()