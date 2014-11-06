
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from site_content_tests import Test_POST_Site_Content
from site_content_tests import Test_GET_Site_Content
from site_content_tests import Test_PUTPATCH_Site_Content
from site_content_tests import Test_DELETE_Site_Content

from site_content_tests import Test_GET_Site_Content_ProtectiveMarking

from feedback_tests import Test_POST_Feedback
from feedback_tests import Test_PUT_Feedback
from feedback_tests import Test_GET_Feedback

from feedback_tests import Test_POST_Comment_On_Public_Feedback
from feedback_tests import Test_GET_Comments_On_Public_Feedback
from feedback_tests import Test_GET_Feedback_Protective_Marking

# Commented because not currently supporting private feedback due to issue with auth on nested subdocuments.
#from feedback_tests import Test_POST_Comment_On_Private_Feedback
