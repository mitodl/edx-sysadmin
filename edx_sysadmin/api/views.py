import json
import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from edx_sysadmin.api.decorators import authenticate_github_request
from edx_sysadmin.git_import import add_repo
from edx_sysadmin.utils.utils import (
    get_local_active_branch,
    get_local_course_repo,
)

from git import Repo, InvalidGitRepositoryError, NoSuchPathError


logger = logging.getLogger(__name__)


@method_decorator(authenticate_github_request(), name="post")
class GitReloadAPIView(APIView):
    """
    APIView to reload courses from github on triggering github webhook
    """

    def post(self, request):
        """
        Trigger for github webhooks for course reload
        """
        message = ""
        try:
            if request.headers.get("X-Github-Event") == "push":
                payload = json.loads(request.POST.get("payload"))
                repo_name = payload["repository"]["name"]

                repo = get_local_course_repo(repo_name)
                if repo:
                    active_branch = get_local_active_branch(repo)
                    pushed_branch = payload.get("ref", "")
                    if active_branch and active_branch == pushed_branch:
                        repo_ssh_url = payload["repository"]["ssh_url"]
                        if repo_ssh_url:
                            add_repo.delay(repo_ssh_url)
                            message = (
                                f"Git reload feature has been triggered for"
                                f" repo: {repo_name} and branch: {active_branch}"
                            )
                            logger.info(message)
                            return Response(
                                {"message": message},
                                status=status.HTTP_200_OK,
                            )
                        else:
                            message = "Request Payload is not appropriate"
                    else:
                        message = f"The pushed branch ({pushed_branch}) is not currently in use"
                else:
                    message = f"The course repo ({repo_name}) is not in use"
            else:
                message = "The API works for 'Push' events only"
        except Exception as e:
            logger.exception(str(e))
            message = f"Request Payload is not appropriate"

        logger.exception(message)
        return Response(
            {"message": message},
            status=status.HTTP_400_BAD_REQUEST,
        )
