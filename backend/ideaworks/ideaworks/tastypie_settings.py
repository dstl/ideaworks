
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

"""
settings specific to the API - what fields get served up
under what different data level?
"""

# Which fields to provide as part of the response.
# The keys (less, more, etc) are provided as url parameters
RESPONSE_FIELDS = {'min' : [ 'id',
                             'title',
                             'modified',
                             'informal_modified',
                             'contributor_name',
                             ],
                   
                   'less' : ['contributor_name',
                             'id',
                             'title',
                             'created',
                             'informal_created',
                             'comment_count',
                             'like_count',
                             'dislike_count',
                             'tag_count',
                             'tags',
                             'pretty_pm',
                             'classification_short',
                             #'protective_marking',  # Required for deriving max_pm field
                             'status',
                             'user_voted',
                             'vote_score'
                             ],

                   'proj_less' : ['contributor_name',
                                 'id',
                                 'title',
                                 'created',
                                 'informal_created',
                                 'comment_count',
                                 'back_count',
                                 'tag_count',
                                 'tags',
                                 'pretty_pm',
                                 'classification_short',
                                 #'protective_marking',  # Required for deriving max_pm field
                                 'status',
                                 'user_backed',
                                  'related_ideas'
                                 ],
                   
                   'more' : ['contributor_name',
                             'id',
                             'title',
                             'created',
                             'informal_created',
                             'description_snippet', # An html-tag stripped + truncated version with ... suffix
                             'comment_count',
                             'like_count',
                             'dislike_count',
                             'tag_count',
                             'tags',
                             #'protective_marking',  # Required for deriving max_pm field
                             'classification_short',
                             'pretty_pm',
                             'status',
                             'user_voted',
                             'vote_score'
                             ],

                   'proj_more' : ['contributor_name',
                                  'id',
                                  'title',
                                  'created',
                                  'informal_created',
                                  'description_snippet', # An html-tag stripped + truncated version with ... suffix
                                  'comment_count',
                                  'back_count',
                                  'tag_count',
                                  'tags',
                                  #'protective_marking',  # Required for deriving max_pm field
                                  'classification_short',
                                  'pretty_pm',
                                  'status',
                                  'user_backed',
                                  'related_ideas'
                                  ],

                   
                   # For list view          
                   'list' : ['contributor_name',
                             'id',
                             'title',
                             'created',
                             'informal_created',
                             'comment_count',
                             'like_count',
                             'dislike_count',
                             'tag_count',
                             'tags',
                             'pretty_pm',
                             'classification_short',
                             #'protective_marking',  # Required for deriving max_pm field
                             'status',
                             'user_voted',
                             'vote_score'],

                   'proj_list' : ['contributor_name',
                                  'id',
                                  'title',
                                  'created',
                                  'informal_created',
                                  'comment_count',
                                  'back_count',
                                  'tag_count',
                                  'tags',
                                  'pretty_pm',
                                  'classification_short',
                                  #'protective_marking',  # Required for deriving max_pm field
                                  'status',
                                  'user_backed',
                                  'related_ideas'
                                  ],
                   # This is just here for the unit tests to make sure we get what we request.
                   'test' : ['id',
                             'title',
                             'informal_created',
                             'description',
                             'comment_count',
                             'like_count',
                             'dislike_count',
                             'protective_marking'
                             ],
                   
                   'proj_test' : ['id',
                                  'title',
                                  'informal_created',
                                  'description',
                                  'comment_count',
                                  'back_count',
                                  'protective_marking'
                             ]}