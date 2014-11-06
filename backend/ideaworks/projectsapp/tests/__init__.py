
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from project_tests import Test_Simple_GET_Project_API
from project_tests import Test_Filtered_GET_Project_API
from project_tests import Test_Filtered_GET_Project_API_modified_status
from project_tests import Test_POST_Project_API
from project_tests import Test_Project_Sorting
from project_tests import Test_GET_tags
from project_tests import Test_Back_Actions
from project_tests import Test_Check_Modified
from project_tests import Test_Data_Level_Responses
from project_tests import Test_Basic_Authentication_Functions
from project_tests import Test_Simple_GET_Project_specifics
from project_tests import Test_Contributor_Naming
from project_tests import Test_Project_With_Protective_Markings
from project_tests import Test_Get_All_PMs
from project_tests import Test_Max_PM_in_Meta
from project_tests import Test_Deletes
from project_tests import Test_Get_Non_Standard_Fields

# Basic functional tests against the API support functions
from project_tests import Test_Basic_API_Functions 

# Tests to cover RSS behaviour
from rss_tests import Test_Project_RSS_Format
from rss_tests import Test_Project_RSS_Modifications
from rss_tests import Test_Project_RSS_Filtering
