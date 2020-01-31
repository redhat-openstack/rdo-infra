import pytest
import unittest


class TestGeneral(unittest.TestCase):

    @pytest.mark.xfail(reason="Not implemented")
    def test_conditional_run_true(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_conditional_run_false(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def expand_dlrn_config(self):
        assert False


class TestStagingRepo(unittest.TestCase):

    @pytest.mark.xfail(reason="Not implemented")
    def test_create_success(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_create_dir_exist(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_staged_promotion_error(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_staged_promotion_link_exists(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_stage_promotion_success(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_create_additional_files(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_create_commit_hierarchy_dir_exist(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_create_commit_hierarchy_component_mode(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_create_commit_hierarchy_single_mode(self):
        assert False


class TestDlrnStagingServer(unittest.TestCase):

    @pytest.mark.xfail(reason="Not implemented")
    def test_create_db_success(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_create_db_error(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_run_server_failure(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_run_server_started_no_connection(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_run_server_success_component_mode(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_run_server_success_single_mode(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_promote_aggregate_rerun_wait_one_sec(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_promote_aggregate_promotion_commit(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_promote_aggregate_no_promotion_commit(self):
        """
        If the commit is not marked as promotion candidate we should not vote
        success for the secondo job
        :return:
        """
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_run_server_already_running(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_setup_success_component_mode(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_setup_success_single_mode(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_setup_success(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_setup_dir_exist(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_teardown_server_kill_fail(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_teardown_server_killed_port_still_open(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_teardown_success(self):
        assert False

    @pytest.mark.xfail(reason="Not implemented")
    def test_stage_info(self):
        assert False
