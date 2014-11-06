
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

"""
Hook up the resources via the tastytools documentation
"""
# Tastytools is used to automatically build API documentation
from tastytools.api import Api

# Create a new API that binds together the existing APIs
v1_api = Api(api_name='v1')


# --- IDEA API ---

from ideasapp.api import IdeaResource
from ideasapp.api import CommentResource
from ideasapp.api import TagResource
from ideasapp.api import ProtectiveMarkingResource
v1_api.register(CommentResource())
v1_api.register(TagResource())
v1_api.register(ProtectiveMarkingResource())

# --- PROJECTS API ---

from projectsapp.api import ProjectResource
from projectsapp.api import CommentResource
from projectsapp.api import TagResource
from projectsapp.api import ProtectiveMarkingResource
v1_api.register(ProjectResource())
v1_api.register(IdeaResource())
v1_api.register(CommentResource())
v1_api.register(TagResource())
v1_api.register(ProtectiveMarkingResource())


# --- CONTENT API ---

from contentapp.api import ProtectiveMarkingResource
from contentapp.api import SiteContentResource
from contentapp.api import FeedbackResource
from contentapp.api import FeedbackCommentResource
v1_api.register(SiteContentResource())
v1_api.register(FeedbackResource())
v1_api.register(FeedbackCommentResource())
v1_api.register(ProtectiveMarkingResource())


# --- Protective Marking API ---

from protective_marking_app.api import ClassificationResource
from protective_marking_app.api import DescriptorResource
from protective_marking_app.api import CodewordResource
from protective_marking_app.api import NationalCaveatResource
from protective_marking_app.api import CssStyleResource
v1_api.register(ClassificationResource())
v1_api.register(DescriptorResource())
v1_api.register(CodewordResource())
v1_api.register(NationalCaveatResource())
v1_api.register(CssStyleResource())


# --- CONFIG/SETTINGS API ---

from config_app.api import ConfigResource
v1_api.register(ConfigResource())

