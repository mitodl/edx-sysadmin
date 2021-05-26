import json
import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from edx_sysadmin.api.permissions import GithubWebhookPermission
from edx_sysadmin.git_import import add_repo
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
            repo_ssh_url = payload["repository"]["ssh_url"]
            repo_name = payload["repository"]["name"]
            pushed_branch = payload.get("ref", "")

            if not event == "push":
                err_msg = _("The API works for 'Push' events only")
            elif not repo_name:
                err_msg = _("Couldn't find Repo's name in the payload")
            elif not repo_ssh_url:
                err_msg = _("Couldn't find Repo's ssh_url in the payload")
            elif not pushed_branch:
                err_msg = _("Couldn't find Repo's pushed branch ref in the payload")
            else:
                repo = get_local_course_repo(repo_name)
                if not repo:
                    err_msg = _("The course repo ({}) is not in use").format(repo_name)
                else:
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
                        logger.info(f"{self.__class__.__name__}:: {msg}")
                        return Response(
                            {"message": msg},
                            status=status.HTTP_200_OK,
                        )

        except Exception as e:
            err_msg = str(e)

        logger.exception(f"{self.__class__.__name__}:: {err_msg}")
        return Response(
            {"message": err_msg},
            status=status.HTTP_400_BAD_REQUEST,
        )
