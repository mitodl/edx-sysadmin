import json
import logging
from path import Path as path
import subprocess

from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from rest_framework import status, permissions
from rest_framework.authentication import SessionAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response

from edx_sysadmin.api.permissions import GithubWebhookPermission
from edx_sysadmin.git_import import (
    add_repo,
    DEFAULT_GIT_REPO_DIR,
    DEFAULT_GIT_REPO_PREFIX,
)
from edx_sysadmin.utils.utils import (
    get_local_active_branch,
    get_local_course_repo,
)


logger = logging.getLogger(__name__)


class GitReloadAPIView(APIView):
    """
    APIView to reload courses from github on triggering github webhook
    """

    permission_classes = [GithubWebhookPermission]

    def post(self, request):
        """
        Trigger for github webhooks for course reload
        """
        err_msg = ""
        try:
            event = request.headers.get("X-Github-Event")
            payload = json.loads(request.body)
            repo_ssh_url = payload["repository"].get("ssh_url")
            repo_clone_url = payload["repository"].get("clone_url")
            repo_name = payload["repository"].get("name")
            pushed_branch = payload.get("ref", "")

            if not event == "push":
                err_msg = _("The API works for 'Push' events only")
            elif not repo_name:
                err_msg = _("Couldn't find Repo's name in the payload")
            elif not repo_ssh_url and not repo_clone_url:
                err_msg = _("Couldn't find Repo's ssh_url or clone_url in the payload")
            elif not pushed_branch:
                err_msg = _("Couldn't find Repo's pushed branch ref in the payload")
            else:
                repo = get_local_course_repo(repo_name)
                if not repo:
                    # New course reload trigger received from a repo but we don't have it's local copy.
                    # We will do the course import for the pushed branch instead

                    # Get the pushed branch from payload
                    branch_name = pushed_branch.replace(DEFAULT_GIT_REPO_PREFIX, "")
                    add_repo.delay(repo=repo_clone_url, branch=branch_name)
                    msg = _(
                        "No local course copy found. Triggered course import for branch: {} of repo: {}"
                    ).format(pushed_branch, repo_name)
                    return self.get_reload_response(
                        msg=msg, status_code=status.HTTP_200_OK
                    )

                else:
                    # We have an existing local copy of the course, so we will reload the course after making sure that
                    # the reload trigger is from the same branch that was used to import the course initially

                    active_branch = get_local_active_branch(repo)
                    if not active_branch or not active_branch == pushed_branch:
                        err_msg = _(
                            "The pushed branch ({}) is not currently in use"
                        ).format(pushed_branch)
                    else:
                        add_repo.delay(repo_ssh_url)
                        msg = _("Triggered reloading branch: {} of repo: {}").format(
                            active_branch, repo_name
                        )
                        return self.get_reload_response(
                            msg=msg, status_code=status.HTTP_200_OK
                        )

        except Exception as e:
            err_msg = str(e)

        return self.get_reload_response(
            msg=err_msg, status_code=status.HTTP_400_BAD_REQUEST
        )

    def get_reload_response(self, msg, status_code):
        if status_code == status.HTTP_200_OK:
            logger.info(f"{self.__class__.__name__}:: {msg}")
        else:
            logger.exception(f"{self.__class__.__name__}:: {msg}")

        return Response(
            {"message": msg},
            status=status_code,
        )


class GitCourseDetailsAPIView(APIView):
    """
    APIView to get git related details of list of courses
    """

    authentication_classes = [SessionAuthentication]
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        """
        Get git related details of list of courses
        """
        try:
            course_dir = request.GET.get("courseDir")
            if course_dir:
                return Response(
                    self.git_info_for_course(course_dir),
                    status=status.HTTP_200_OK,
                )
            else:
                err_msg = "Course directory name is required"

        except Exception as e:
            err_msg = str(e)

        logger.exception(f"{self.__class__.__name__}:: {err_msg}")
        return Response(
            {"message": err_msg},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def git_info_for_course(self, course_dir):
        """This pulls out some git info like the last commit"""

        git_dir = settings.DATA_DIR / course_dir

        # Try the data dir, then try to find it in the git import dir
        if not git_dir.exists():
            git_repo_dir = getattr(settings, "GIT_REPO_DIR", DEFAULT_GIT_REPO_DIR)
            git_dir = path(git_repo_dir) / course_dir
            if not git_dir.exists():
                return ["", "", ""]

        cmd = [
            "git",
            "log",
            "-1",
            '--format=format:{ "commit": "%H", "author": "%an %ae", "date": "%ad"}',
        ]
        try:
            output_json = json.loads(
                subprocess.check_output(cmd, cwd=git_dir).decode("utf-8")
            )
        except OSError as error:
            logger.warning("Error fetching git data: %s - %s", course_dir, error)
            raise
        except (ValueError, subprocess.CalledProcessError):
            raise

        return output_json
