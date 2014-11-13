/* (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK */

'use strict';

/************************************************************************
 *  Controllers
 *    ideaworks.ngControllers
 *************************************************************************/

ideaworks.ngControllers = angular.module('ideaworks.ngControllers', []);


/************************************************************************
 *  appCtrl
 *    Bound to <body> tag and used as main controller for shared functions
 *    and variables
 *************************************************************************/
ideaworks.ngControllers.controller('appCtrl', ['$rootScope', '$scope', '$http', '$cookies', '$cacheFactory', '$window', '$location', '$route', 'Ideas', 'Projects', 'User', 'ProtectiveMarking', 'Config', 'Content',
    function ($rootScope, $scope, $http, $cookies, $cacheFactory, $window, $location, $route, Ideas, Projects, User, ProtectiveMarking, Config, Content) {

      /* global $rootScope variables */
      // errorUrl - used to store URL of any 404 to show on error page
      $rootScope.errorUrl = "";

      // previousViewUrl - used to store the view url so the close button takes user back to correct view
      $rootScope.previousViewUrl = "";
      $rootScope.currentView = "";

      // currentContext - used to store the form or view type for current route - e.g idea or project or feedback etc...
      $rootScope.currentContext = "ideas";

      // deleteType - used to store type of deletion (idea, project, comment etc...)
      $rootScope.deleteType = "";

      
      /********** Common functions *********/

      // sets the previousViewUrl to current url
      $scope.setPreviousViewUrl = function () {
        $rootScope.previousViewUrl = $location.url();
      }

      // loads the previousViewUrl if available, otherwise opens default page
      $scope.openPreviousViewUrl = function (forceRefresh) {
        if ($rootScope.previousViewUrl === '') {
          $window.location.href = Config.frontEndPath;
        } else {
          if (forceRefresh) {
            $window.location.href = '/#' + $rootScope.previousViewUrl;
          } else {
            $location.url($rootScope.previousViewUrl);
            $rootScope.previousViewUrl = "";
          }
        }
      }

      // closes popup alert modal
      $scope.closePopupAlert = function () {
        $('.popup-alert').hide();
        $('.popup-alert-mask').hide();
      }

      // share idea via mailto: link
      $scope.shareIdeaEmail = function (idea) {
        var subject = encodeURIComponent('Here\'s an idea you might find interesting'),
        line1 = encodeURIComponent('I thought you might find the following idea interesting.'),
        line2 = encodeURIComponent('"' + idea.title + '"'),
        line3 = encodeURIComponent('Submitted ' + idea.informal_created + ' by ' + idea.contributor_name),
        line4 = encodeURIComponent('Use the link below to open the idea'),
        line5 = encodeURIComponent($location.absUrl()),
        linebreak = '%0D%0A%0D%0A';
        window.location.href = 'mailto:?subject=' + subject + '&body=' + line1 + linebreak + line2 + linebreak + line3 + linebreak + line4 + linebreak + line5;
      }

      // share project via mailto: link
      $scope.shareProjectEmail = function (project) {
        var subject = encodeURIComponent('Here\'s a project you might find interesting'),
        line1 = encodeURIComponent('I thought you might find the following project interesting.'),
        line2 = encodeURIComponent('"' + project.title + '"'),
        line3 = encodeURIComponent('Submitted ' + project.informal_created + ' by ' + project.contributor_name),
        line4 = encodeURIComponent('Use the link below to open the project'),
        line5 = encodeURIComponent($location.absUrl()),
        linebreak = '%0D%0A%0D%0A';
        window.location.href = 'mailto:?subject=' + subject + '&body=' + line1 + linebreak + line2 + linebreak + line3 + linebreak + line4 + linebreak + line5;
      }
      
      // creates a new idea if user is not anonymous
      $scope.createIdea = function (user) {
        // Stop if user is not logged in
        if (user.name() === 'Anonymous') {
          $('.anonymous-action').fadeIn();
          $('.popup-alert-mask').show();
          return false;
        }
        $scope.setPreviousViewUrl();
        $window.location.href = Config.frontEndPath + '/#/ideas/create';
      }

      // creates a new project but only if user has the staff role
      $scope.createProject = function () {
        // Stop if user does not have staff role
        if (!$scope.user.isStaff) {
          $('.anonymous-action').fadeIn();
          $('.popup-alert-mask').show();
          return false;
        }
        $scope.setPreviousViewUrl();
        $window.location.href = Config.frontEndPath + '/#/projects/create';
      }

      // creates new feedback if user is not anonymous
      $scope.createFeedback = function (user) {
        // Stop if user is not logged in
        if (user.name() === 'Anonymous') {
          $('.anonymous-action').fadeIn();
          $('.popup-alert-mask').show();
          return false;
        }
        $window.location.href = Config.frontEndPath + '/#/feedback/create';
      }
      
      // refreshes the current view
      $scope.refresh = function (type) {
        if (type !== undefined && type === 'page') {
          // Refresh entire page
          $window.location.reload();
        } else {
          // Refresh the view
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $route.reload();
        }
      }

      
      /********** User functions ***********/
      $scope.user = {};
      
      // return user id from cookie
      $scope.user.id = function () {
        return $cookies['user_id'] ? $cookies['user_id'] : '0';
      }

      // name and email cookies returned in "double quotes" so strip off and replace via regex
      $scope.user.name = function () {
        // if admin/super-user there may only be an id, if so use that as a name
        if ($cookies['user_name'] == '" "') {
          return $cookies['user_id'];
        } else {
          return $cookies['user_name'] ? $cookies['user_name'].replace(/(^"|"$)/g, '') : 'Anonymous';
        }
      }

      // return user email
      $scope.user.email = function () {
        return $cookies['user_email'] ? $cookies['user_email'].replace(/(^"|"$)/g, '') : '';
      }
      
      // hasRole - return true/false for given role
      $scope.user.hasRole = function (role) {
        var rolesCookie = $cookies['user_roles'] ? $cookies['user_roles'].replace(/(^"|"$)/g, '') : '';
        var roles = rolesCookie.replace(/\\054/g, ',').split(',');
        if ($.inArray(role, roles) !== -1) {
          return true;
        } else {
          return false;
        }
      }
      
      // shorthand vars for checking user roles
      $scope.user.isAdmin = $scope.user.hasRole('super');
      $scope.user.isStaff = $scope.user.hasRole('staff');

      // open user login page
      $scope.user.login = function () {
        $window.location.href = Config.appPath + '/accounts/login/?next=' + $location.protocol() + '://' + $location.host() + Config.frontEndPath + '/%23' + $location.url();
      }

      // logout current user
      $scope.user.logout = function () {
        // clear cookies and redirect to logged out page
        $.removeCookie('user_id', {
          path : '/'
        });

        $.removeCookie('user_name', {
          path : '/'
        });
        $.removeCookie('user_email', {
          path : '/'
        });
        $.removeCookie('user_active', {
          path : '/'
        });
        $.removeCookie('user_roles', {
          path : '/'
        });
        $.removeCookie('api_key', {
          path : '/'
        });
        $.removeCookie('csrftoken', {
          path : '/'
        });
        $window.location.href = Config.appPath + '/accounts/logout/?next=' + $location.protocol() + '://' + $location.host() + '/%23/logged-out';
      }
      
      // register user
      $scope.user.register = function () {
        $window.location.href = Config.appPath + '/accounts/register/?next=' + $location.protocol() + '://' + $location.host() + Config.frontEndPath;
      }

      // change password
      $scope.user.changePassword = function () {
        $window.location.href = Config.appPath + '/accounts/password/change/?next=' + $location.protocol() + '://' + $location.host() + Config.frontEndPath + '/%23' + $location.url();
      }

      // get users idea count(s)
      // if user id available (user logged in) then get their idea/project and draft idea/project counts
      $scope.user.getIdeasCounts = function () {
        if ($scope.user.id() !== '0') {
          var userViewParams = {};
          userViewParams.data_level = 'meta';
          userViewParams.limit = 0;
          userViewParams.status = 'published';
          userViewParams.user = $scope.user.id();

          // get the count of published ideas for this user
          Ideas.get(userViewParams, function (data) {
            $scope.user.ideasCount = data.meta.total_count;
            // then get the draft count
            userViewParams.status = 'draft';
            Ideas.get(userViewParams, function (data) {
              $scope.user.draftIdeasCount = data.meta.total_count;
            });
          });

          // get the count of published projects for this user
          Projects.get(userViewParams, function (data) {
            $scope.user.projectsCount = data.meta.total_count;
            // then get the draft count
            userViewParams.status = 'draft';
            Projects.get(userViewParams, function (data) {
              $scope.user.draftProjectsCount = data.meta.total_count;
            });
          });

        }
      }

      // get counts on loading
      $scope.user.getIdeasCounts();

      // TBC
      $scope.user.loadProfile = function (userId) {
        // this is a placeHolder function - tbc...
        // will load a given user's page/ideas/profile...
      }

      
      /********** Protective Marking ***********/
      // Load and initialise the protective marking data

      $scope.pm = {}

      // build $scope.pm.classifications obj - e.g $scope.pm.classifications['PRIVATE']
      ProtectiveMarking.get('classifications').success(function (data) {
        $scope.pm.classifications = {};
        $scope.pm.classifications.list = [];
        angular.forEach(data, function (classification, key) {
          if (classification.active) {
            // add classification only to list item
            var pmListItem = {};
            pmListItem.value = classification.abbreviation;
            pmListItem.text = classification.classification;

            // $scope.pm.classifications.list.push(classification.classification);
            $scope.pm.classifications.list.push(pmListItem);
            // add all supplementary data
            var abbr = classification.abbreviation.toUpperCase();
            $scope.pm.classifications[abbr] = {};
            $scope.pm.classifications[abbr].abbreviation = abbr;
            $scope.pm.classifications[abbr].classification = classification.classification;
            $scope.pm.classifications[abbr].coment = classification.comment;
            $scope.pm.classifications[abbr].source = classification.source;
            $scope.pm.classifications[abbr].css_style = classification.css_style;
            $scope.pm.classifications[abbr].national_authority = classification.national_authority;
            $scope.pm.classifications[abbr].rank = classification.rank;
            // build the css needed as a single string based on the css_style
            var css = '';
            angular.forEach(classification.css_style, function (value, element) {
              css += element + ':' + value + ';';
            });
            $scope.pm.classifications[abbr].css = css;
            $scope.pm.classifications[abbr].colour = classification.css_style['background-color'];
            // set the css class name
            $scope.pm.classifications[abbr].class_name = classification.classification.replace(/ +/g, '-').toLowerCase();
          }
        })
      });

      // build $scope.pm.codewords obj
      ProtectiveMarking.get('codewords').success(function (data) {
        $scope.pm.codewords = {};
        $scope.pm.codewords.list = [];
        angular.forEach(data, function (codeword, key) {
          if (codeword.active) {
            // add codeword only to list item
            $scope.pm.codewords.list.push(codeword.codeword);
            // add all supplementary data
            $scope.pm.codewords[codeword.codeword] = {};
            $scope.pm.codewords[codeword.codeword].abbreviation = codeword.abbreviation;
            $scope.pm.codewords[codeword.codeword].coment = codeword.comment;
            $scope.pm.codewords[codeword.codeword].source = codeword.source;
            $scope.pm.codewords[codeword.codeword].national_authority = codeword.national_authority;
          }
        })
      });

      // build $scope.pm.descriptors obj
      ProtectiveMarking.get('descriptors').success(function (data) {
        $scope.pm.descriptors = {};
        $scope.pm.descriptors.list = [];
        angular.forEach(data, function (descriptor, key) {
          if (descriptor.active) {
            // add descriptor only to list item
            $scope.pm.descriptors.list.push(descriptor.descriptor);
            // add all supplementary data
            $scope.pm.descriptors[descriptor.descriptor] = {};
            $scope.pm.descriptors[descriptor.descriptor].coment = descriptor.comment;
            $scope.pm.descriptors[descriptor.descriptor].source = descriptor.source;
            $scope.pm.descriptors[descriptor.descriptor].national_authority = descriptor.national_authority;
          }
        })
      });

      // build $scope.pm.national_caveats obj
      ProtectiveMarking.get('national_caveats').success(function (data) {
        $scope.pm.national_caveats = {};
        $scope.pm.national_caveats.list = [];
        angular.forEach(data, function (national_caveat, key) {
          if (national_caveat.active) {
            // add national_caveat only to list item
            $scope.pm.national_caveats.list.push(national_caveat.primary_name);
            // add all supplementary data
            $scope.pm.national_caveats[national_caveat.primary_name] = {};
            $scope.pm.national_caveats[national_caveat.primary_name].secondary_names = national_caveat.secondary_names;
            $scope.pm.national_caveats[national_caveat.primary_name].member_countries = national_caveat.member_countries;
            $scope.pm.national_caveats[national_caveat.primary_name].rank = national_caveat.rank;
            $scope.pm.national_caveats[national_caveat.primary_name].coment = national_caveat.comment;
            $scope.pm.national_caveats[national_caveat.primary_name].source = national_caveat.source;
          }
        })
      });

      
      /*********** Tag filtering ***********/

      $scope.filterTag = false;
      $scope.filterTags = [];

      // filter by given tag
      $scope.filterByTag = function (tag) {

        if (tag === '') {
          $scope.filterTag = false;
          $scope.filterTagDisplay = '';
          $scope.filterTags = [];
          // clear the filtering by loading plain view
          $location.url('/' + $rootScope.currentContext + '/view-all/summary/');
        } else {
          var hasTag = $.inArray(tag, $scope.filterTags);

          if (hasTag === -1) {
            $scope.filterTags.push(tag);
          } else {
            $scope.filterTags.splice(hasTag, 1);
          }

          var vPath = '/' + $rootScope.currentContext + '/view-all';
          var vLayout = 'summary';

          if ($scope.viewPath !== undefined) {
            vPath = $scope.viewPath
          }

          if ($scope.viewLayout !== undefined) {
            vLayout = $scope.viewLayout
          }

          if ($scope.filterTags.length === 0) {
            $scope.filterTag = false;
            $scope.filterTagDisplay = '';
            // clear the filtering by loading plain view
            $location.url(vPath + '/' + vLayout + '/');
          } else {
            $scope.filterTag = true;
            $scope.filterTagDisplay = $scope.filterTags.join(', ');
            $location.url(vPath + '/' + vLayout + '/?tags__in=' + $scope.filterTags.join(','));
          }

        }
      };

      // checks if given tag is selected
      $scope.isTagSelected = function (tag) {
        if ($.inArray(tag, $scope.filterTags) === -1) {
          return false;
        } else {
          return true;
        }
      };
      
      
      // get the content types from the JSON file
      $scope.getTypesPromise = Content.getTypes();
      
      $scope.getTypesPromise.then(function (t) {
        $scope.siteContentTypes = t.data;
      });

      
      /* For CSRF token compatibility with Django */
      $http.defaults.headers.common['X-CSRFToken'] = $cookies['csrftoken'];
      $http.defaults.headers.common['Authorization'] = 'ApiKey ' + $cookies['user_id'] + ':' + $cookies['api_key'];
      
      
    }
  ]);

  
/************************************************************************
 *  IdeasViewCtrl
 *    used by: ../ideas/view , view-all  , view-latest, view-popular
 *
 *************************************************************************/
ideaworks.ngControllers.controller('IdeasViewCtrl', ['$rootScope', '$scope', '$routeParams', '$location', '$route', '$modal', '$filter', 'User', 'Ideas', 'Vote', 'Tags', 'Comment',
    function ($rootScope, $scope, $routeParams, $location, $route, $modal, $filter, User, Ideas, Vote, Tags, Comment) {

      // set the currentContext
      $rootScope.currentContext = "ideas";

      // get the list of published tags
      $scope.tags = Tags.get({
          status : 'published'
        });

      $scope.tagFilterType = 'multiple';

      $scope.setTagFilterType = function (type) {
        $scope.tagFilterType = type;
      }

      // include shared functions and services from Vote in services.js
      $scope.vote = Vote;

      // include shared functions and services from Comment in services.js
      $scope.comment = Comment;

      // get the view path, type and layout from the URL
      $scope.viewPath = $location.path().slice(0, $location.path().lastIndexOf('/'));
      $scope.viewName = $scope.viewPath.split('/').pop();
      $scope.viewLayout = $location.path().split('/').pop();
      $scope.viewParams = $location.url().split('?')[1] ? '/?' + $location.url().split('?')[1] : '';

      // number of latest/most popular ideas to show
      $scope.viewLatestCount = 5;

      // default view count
      $scope.viewDefaultCount = 20;

      // default view sort order
      $scope.viewDefaultOrderBy = '-created';

      // default view status
      $scope.viewDefaultStatus = 'published';
      $scope.status = $routeParams.status ? $routeParams.status : $scope.viewDefaultStatus;
      $scope.status = $routeParams.status__in ? 'all' : $scope.status;

      // default user filter
      $scope.viewDefaultUser = null;
      $scope.viewCurrentUser = $routeParams.user ? $routeParams.user : $scope.viewDefaultUser;

      $scope.viewIsLoading = true;

      $scope.doViewLoaded = function () {
        $scope.viewIsLoading = false;
      };

      // default view params, use values in query-string, otherwise use default values
      var viewParams = {
        limit : $routeParams.limit ? $routeParams.limit : $scope.viewDefaultCount, // number of records to load
        offset : $routeParams.offset ? $routeParams.offset : 0, // start point (for paging)
        order_by : $routeParams.order_by ? $routeParams.order_by : $scope.viewDefaultOrderBy, // sort order
        status : $routeParams.status ? $routeParams.status : $scope.viewDefaultStatus, // status
        user : $routeParams.user ? $routeParams.user : $scope.viewDefaultUser // user
      };
      $rootScope.currentView = $scope.viewName + '-' + viewParams.status;

      if ($routeParams.status === 'all' || $routeParams.status__in) {
        delete(viewParams.status);
      }

      if ($routeParams.status__in) {
        viewParams.status__in = $routeParams.status__in;
      }

      if ($routeParams.tags__in) {
        viewParams.tags__in = $routeParams.tags__in;
      }

      // if $scope.viewName is view-latest (and no limit in URL) then show latest $scope.viewLatestCount ideas
      if ($scope.viewName === 'view-latest') {
        viewParams.limit = $routeParams.limit ? $routeParams.limit : $scope.viewLatestCount;
        $scope.orderProp = '-created';
      }

      // if $scope.viewName is view-all (and no limit in URL) then show all
      if ($scope.viewName === 'view-all') {
        viewParams.limit = $routeParams.limit ? $routeParams.limit : 0;
        $scope.orderProp = '-created';
      }

      // if $scope.viewName is view-popular then sort by vote_score
      if ($scope.viewName === 'view-popular') {
        viewParams.limit = $routeParams.limit ? $routeParams.limit : $scope.viewLatestCount;
        viewParams.order_by = '-vote_score';
        $scope.orderProp = '-vote_score';
      }

      // get the ideas..
      Ideas.get(viewParams, function (data) {
        if (data.meta.total_count === 0) {
          $scope.doViewLoaded();
          $('.view-body').html('<div class="alert alert-danger"><strong>No ideas found</strong><p>Please select another view.</p></div>');
        } else {
          // get maximum protective marking
          $scope.max_pm = data.meta.max_pm;
          $scope.ideasData = data;
          $scope.ideasCount = data.meta.total_count;
          if ($scope.viewLatestCount > $scope.ideasCount) {
            $scope.ideasDisplayCount = $scope.ideasCount
          } else {
            $scope.ideasDisplayCount = $scope.viewLatestCount;
          }
          $scope.ideas = [];
          $scope.ideasList = [];

          angular.forEach(data.objects, function (idea, key) {
            // calculate the like/dislike percentages for use in the likeBar visualisation
            idea.like_percent = Math.round((idea.like_count / (idea.like_count + idea.dislike_count) * 100));
            idea.dislike_percent = 100 - idea.like_percent;

            idea.tag_list = idea.tags.join(', ');

            if (idea.contributor_name === ' ') {
              idea.contributor_name = "Admin"
            }

            $scope.ideas.push(idea);

            // separate copy for list view (needed for filtering)
            $scope.ideasList = $scope.ideas;

          });
        }
      });

      // filter clearing
      $scope.clearIdeasFilter = function () {
        $scope.filterOptions.filterText = '';
      };

      $scope.clearIdeasListFilter = function () {
        $scope.filterList = '';
      };

      $scope.clearTagsFilter = function () {
        $scope.tags.filterText = '';
      };

      
      /*********** ng-grid stuff ***********/
      // code for the list view

      // Make the title click-able and open the idea in read mode
      var title_cellTemplate = '<div class="ngCellText" ng-class="col.colIndex()"><a ng-href="" ng-click="clickRow(row)"><span ng-cell-text>{{row.getProperty(col.field)}}</span></a></div>';

      // use created value (for correct sorting) but display the informal_created value
      var created_cellTemplate = '<div class="ngCellText" ng-class="col.colIndex()"><span ng-cell-text>{{row.entity.informal_created}}</span></div>';

      // display thumbs up for likes header
      var like_HeaderCellTemplate = '<div class="ngHeaderSortColumn {{col.headerClass}}" ng-style="{\'cursor\': col.cursor}" ng-class="{ \'ngSorted\': !noSortVisible }"><div ng-click="col.sort($event)" ng-class="\'colt\' + col.index" class="ngHeaderText"><i class="icon-thumbs-up icon-white like"></i></div><div class="ngSortButtonDown" ng-show="col.showSortButtonDown()"></div><div class="ngSortButtonUp" ng-show="col.showSortButtonUp()"></div><div class="ngSortPriority">{{col.sortPriority}}</div><div ng-class="{ ngPinnedIcon: col.pinned, ngUnPinnedIcon: !col.pinned }" ng-click="togglePin(col)" ng-show="col.pinnable"></div></div><div ng-show="col.resizable" class="ngHeaderGrip" ng-click="col.gripClick($event)" ng-mousedown="col.gripOnMouseDown($event)"></div>';

      // display thumbs down for dislikes header
      var dislike_HeaderCellTemplate = '<div class="ngHeaderSortColumn {{col.headerClass}}" ng-style="{\'cursor\': col.cursor}" ng-class="{ \'ngSorted\': !noSortVisible }"><div ng-click="col.sort($event)" ng-class="\'colt\' + col.index" class="ngHeaderText"><i class="icon-thumbs-down icon-white dislike"></i></div><div class="ngSortButtonDown" ng-show="col.showSortButtonDown()"></div><div class="ngSortButtonUp" ng-show="col.showSortButtonUp()"></div><div class="ngSortPriority">{{col.sortPriority}}</div><div ng-class="{ ngPinnedIcon: col.pinned, ngUnPinnedIcon: !col.pinned }" ng-click="togglePin(col)" ng-show="col.pinnable"></div></div><div ng-show="col.resizable" class="ngHeaderGrip" ng-click="col.gripClick($event)" ng-mousedown="col.gripOnMouseDown($event)"></div>';

      // display speech bubble for comments header
      var comment_HeaderCellTemplate = '<div class="ngHeaderSortColumn {{col.headerClass}}" ng-style="{\'cursor\': col.cursor}" ng-class="{ \'ngSorted\': !noSortVisible }"><div ng-click="col.sort($event)" ng-class="\'colt\' + col.index" class="ngHeaderText"><i class="icon-comment"></i></div><div class="ngSortButtonDown" ng-show="col.showSortButtonDown()"></div><div class="ngSortButtonUp" ng-show="col.showSortButtonUp()"></div><div class="ngSortPriority">{{col.sortPriority}}</div><div ng-class="{ ngPinnedIcon: col.pinned, ngUnPinnedIcon: !col.pinned }" ng-click="togglePin(col)" ng-show="col.pinnable"></div></div><div ng-show="col.resizable" class="ngHeaderGrip" ng-click="col.gripClick($event)" ng-mousedown="col.gripOnMouseDown($event)"></div>';

      // filter / search the list view
      $scope.$watch('filterList', function () {
        $scope.ideasList = $filter('filter')($scope.ideas, $scope.filterList);
      });

      $scope.gridOptions = {
        data : 'ideasList',
        enableRowSelection : false,
        columnDefs : [{
            field : 'id',
            visible : false
          }, // just for linking , not displayed
          {
            field : 'title',
            displayName : 'Idea title',
            width : '*******',
            cellTemplate : title_cellTemplate
          }, {
            field : 'created',
            displayName : 'Created',
            width : '***',
            cellTemplate : created_cellTemplate
          }, {
            field : 'title',
            displayName : 'By',
            width : '***'
          }, {
            field : 'tag_list',
            displayName : 'Tags',
            width : '***'
          }, {
            field : 'pretty_pm',
            displayName : 'Classification',
            width : '****'
          }, {
            field : 'like_count',
            width : '40px',
            headerCellTemplate : like_HeaderCellTemplate
          }, {
            field : 'dislike_count',
            width : '40px',
            headerCellTemplate : dislike_HeaderCellTemplate
          }, {
            field : 'comment_count',
            width : '40px',
            headerCellTemplate : comment_HeaderCellTemplate
          }
        ]
      };

      $scope.clickRow = function (row) {
        $scope.openIdea(row.entity.id);
      }

      $scope.sortList = function (sort) {
        $scope.gridOptions.sortBy(sort);
      };

      $scope.$on('ngGridEventData', function (e, s) {
        if ($scope.ideas !== undefined) {
          $scope.doViewLoaded();
        }
      });

      $scope.switchView = function () {
        $('.view-body').html('');
        $scope.filterByTag('');
      }

      $scope.openIdea = function (id) {
        $scope.setPreviousViewUrl();
        $location.url('/ideas/' + id + '/read');
      }

    }
  ]);

  
/************************************************************************
 *  IdeaCreateCtrl
 *    used by: ../ideas/create
 *    Handles new idea form
 *************************************************************************/
ideaworks.ngControllers.controller('IdeaCreateCtrl', ['$scope', '$routeParams', '$location', '$window', '$filter', '$cacheFactory', 'orderByFilter', '$compile', 'Idea', 'Tags',
    function ($scope, $routeParams, $location, $window, $filter, $cacheFactory, orderByFilter, $compile, Idea, Tags) {

      if ($routeParams.ideaId === undefined) {
        $scope.mode = 'create';
      } else {
        $scope.mode = 'edit';
      }

      // create a blank idea obj
      $scope.idea = {};
      $scope.idea.taglist = '';

      if ($scope.mode === 'edit') {

        Idea.get($routeParams.ideaId).success(function (idea) {
          // get maximum protective marking
          $scope.max_pm = idea.meta.max_pm;
          // get idea data
          $scope.idea = idea.objects[0];
          $scope.selectClassification = $scope.idea.protective_marking.classification_short;
          $scope.idea.taglist = $scope.idea.tags.join();

          if ($scope.idea.status === 'hidden') {
            $scope.hideIdea = true;
          }
        });

      } else {
        // its a new idea (create);
        $scope.idea.status = 'new unsaved';

        // create a blank obj for selected tags
        $scope.idea.tags = [];

        $scope.idea.protective_marking = {};
      }
      // check if value is in array
      $scope.isTagInArray = function (tag) {
        if ($scope.idea.taglist !== undefined) {
          return $.inArray(tag, $scope.idea.taglist.split(',')) > -1;
        } else {
          return false
        }
      }
      $scope.idea.submitted = false;

      $scope.updatePM = function () {

        // add the abbreviated classification and rank
        $scope.idea.classification_short = $scope.pm.classifications[$scope.selectClassification].abbreviation;
        $scope.idea.protective_marking.classification_short = $scope.pm.classifications[$scope.selectClassification].abbreviation;
        $scope.idea.protective_marking.classification = $scope.pm.classifications[$scope.selectClassification].classification;
        $scope.idea.protective_marking.classification_rank = $scope.pm.classifications[$scope.selectClassification].rank;

        // National caveats
        if ($scope.idea.protective_marking.national_caveats_primary_name !== undefined) {
          $scope.idea.protective_marking.national_caveats_members = $scope.pm.national_caveats[$scope.idea.protective_marking.national_caveats_primary_name].member_countries;
          $scope.idea.protective_marking.national_caveats_rank = $scope.pm.national_caveats[$scope.idea.protective_marking.national_caveats_primary_name].rank;
        }

        // Codewords
        if ($scope.idea.protective_marking.codewords !== undefined) {
          $scope.idea.protective_marking.codewords_short = [];
          angular.forEach($scope.idea.protective_marking.codewords, function (cw, key) {
            $scope.idea.protective_marking.codewords_short.push($scope.pm.codewords[cw].abbreviation)
          });
        }

      }

      $scope.showPMOptions = function () {
        $('#showMorePM').hide();
        $('#hideMorePM').show();
        $('#pm-options').fadeIn();
      }

      $scope.hidePMOptions = function () {
        $('#showMorePM').show();
        $('#hideMorePM').hide();
        $('#pm-options').fadeOut();
      }

      // get the list of available tags (will return draft and published tags);
      $scope.tags = Tags.get({
          status : 'draft,published,hidden'
        });

      // submit idea
      $scope.submitIdea = function (isValid, status) {
        $scope.idea.submitted = true;
        $scope.idea.status = status;

        if (!isValid) {
          return false;
        }

        // delete idea.taglist and idea.submitted, we don't need these now, were just for form display and validation purposes
        delete($scope.idea.taglist);
        delete($scope.idea.submitted);

        var submittedIdea = Idea.create($scope.idea);
        submittedIdea.success(function (data, status, headers, config) {
          var ideaId = headers().location.split('/idea')[1];
          // open the new idea in read mode
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $location.url('/ideas' + ideaId + 'read');
          $scope.user.getIdeasCounts();
        });
      };

      // save edited idea
      $scope.saveIdea = function (isValid, status) {
        $scope.idea.submitted = true;
        $scope.idea.status = status;

        if (!isValid) {
          return false;
        }

        // delete idea.taglist and idea.submitted, we don't need these now, were just for form display and validation purposes
        delete($scope.idea.taglist);
        delete($scope.idea.submitted);

        var submittedIdea = Idea.edit($scope.idea);
        submittedIdea.success(function (data, status, headers, config) {
          // re-open in read mode
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $location.url('/ideas/' + $scope.idea.id + '/read');
          $scope.user.getIdeasCounts();
        });
      };

      $scope.cancelIdea = function () {
        $scope.openPreviousViewUrl();
      }

      $scope.hiddenIdea = function () {
        var data = {
          'status' : 'hidden'
        };
        Idea.patch($routeParams.ideaId, data).success(function (resp) {
          $scope.openPreviousViewUrl();
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $route.reload();
        });
      }

      // add / remove a selected tag
      $scope.addTag = function ($event) {

        // get a handle on the clicked tag button <a> element
        var $tag = $($event.target);

        // toggle the colour of the button
        if ($tag.hasClass('new-tag')) {
          $tag.toggleClass('btn-success');
        } else {
          $tag.toggleClass('btn-info');
        }
        // get the tag text value
        var tag = $tag.text().replace(/[0-9]/g, "").trim();
        // loop thru current selected tags, if tag clicked is already selected then remove it
        // otherwise add it
        var hasTag = $.inArray(tag, $scope.idea.tags);

        if (hasTag === -1) {
          $scope.idea.tags.push(tag);
        } else {
          $scope.idea.tags.splice(hasTag, 1);
        }

        $scope.idea.taglist = tag;
        if ($scope.idea.taglist.length == 0) {
          $scope.idea.taglist = '';
        } else {
          $scope.idea.taglist = $scope.idea.tags.join();
        }
      };

      $scope.clearFilter = function () {
        $scope.taglistfilter = '';
      };

      $scope.addNewTag = function () {

        if ($scope.taglistfilter === undefined || $scope.taglistfilter.length === 0) {
          return false
        }

        if ($scope.isExistingTag()) {
          $('.tagExistsAlert').fadeIn();
          setTimeout("$('.tagExistsAlert').fadeOut();", 2500);
        } else {
          $('span.tags').prepend($compile('<a class="btn btn-mini btn-tag btn-success new-tag disabled" ng-click="addTag($event)" ng-href="" ng-class="{\'btn-info\':isTagInArray(tag.text)}">' + $scope.taglistfilter + '</a>')($scope));
          $scope.clearFilter();
          setTimeout("$('.tags a')[0].click();", 500);
        }

      }

      // checks for existing tag
      $scope.isExistingTag = function () {
        if ($scope.taglistfilter !== undefined) {
          var newTag = $scope.taglistfilter,
          isExisting = false;
          angular.forEach($scope.tags.objects, function (tag, key) {
            if (newTag == tag.text) {
              isExisting = true;
            }
          });
          return isExisting;
        } else {
          return false
        }
      }

      // force tag sort
      $scope.sortTags = function (sortOpt) {
        $scope.orderProp = sortOpt;
      }

    }
  ]);

  
/************************************************************************
 *  IdeaReadCtrl
 *    used by: ../ideas/:ideaId and ../ideas/:ideaId/read
 *    Handles read version of idea form
 *************************************************************************/
// This controller will handle IDEA READ FORM
ideaworks.ngControllers.controller('IdeaReadCtrl', ['$rootScope', '$scope', '$routeParams', '$route', '$location', '$window', '$cacheFactory', '$modal', 'Idea', 'Vote', 'Comment', 'Config',
    function ($rootScope, $scope, $routeParams, $route, $location, $window, $cacheFactory, $modal, Idea, Vote, Comment, Config) {
     
      $scope.vote = Vote; // include shared functions and services from Vote in services.js
      $scope.comment = Comment; // include shared functions and services from Comment in services.js

      // set the currentContext
      $rootScope.currentContext = "ideas";

      Idea.get($routeParams.ideaId).success(function (idea) {

        // get maximum protective marking
        $scope.max_pm = idea.meta.max_pm;

        // get idea data
        idea = idea.objects[0];
        // calculate the like/dislike percentages for use in the likeBar visualisation
        idea.like_percent = Math.round((idea.like_count / (idea.like_count + idea.dislike_count) * 100));
        idea.dislike_percent = 100 - idea.like_percent;
        $scope.idea = idea;

        if ($scope.idea.user === $scope.user.id()) {
          $scope.user.isAuthor = true;
        } else {
          $scope.user.isAuthor = false;
        }

      });

      $scope.editIdea = function () {
        $window.location.href = Config.frontEndPath + '/#/ideas/' + $scope.idea.id + '/edit'
      }

      $scope.closeIdea = function (forceRefresh) {
        // if no history then just open the default view
        $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
        if ($window.history.length > 1) {
          $scope.openPreviousViewUrl(forceRefresh);
        } else {
          $window.location.href = Config.frontEndPath;
        }
      }

      $scope.confirmSoftDeleteIdea = function () {
        $('.confirm-soft-delete-idea').fadeIn();
        $('.popup-alert-mask').show();
      }

      $scope.confirmDeleteIdea = function () {
        $('.confirm-delete-idea').fadeIn();
        $('.popup-alert-mask').show();
      }

      $scope.softDeleteIdea = function () {
        var data = {
          'status' : 'deleted'
        };
        Idea.patch($routeParams.ideaId, data).success(function (resp) {
          $scope.openPreviousViewUrl();
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $route.reload();
        });
      }

      $scope.deleteIdea = function () {
        $rootScope.deleteType = 'idea';
        Idea.del($routeParams.ideaId).success(function (resp) {
          $rootScope.deleteType = '';
        });
      }

      $scope.deleteComment = function (uri) {
        $rootScope.deleteType = 'comment';
        Comment.del(uri).success(function (resp) {
          $rootScope.deleteType = '';
        });
      }

      $scope.editComment = function (uri) {

        Comment.load(uri).success(function (resp) {
          $scope.commentData = resp;

          var commentModal = $modal.open({
              templateUrl : 'templates/modals/edit-comment.html',
              resolve : {
                cData : function () {
                  return $scope.commentData;
                },
                pm : function () {
                  return $scope.pm;
                }
              },
              controller : function ($scope, $modalInstance, cData, pm) {

                $scope.cData = cData;
                $scope.pm = pm;
                $scope.comment = cData.objects[0];
                $scope.selectCommentClassification = $scope.comment.protective_marking.classification_short;
                $scope.commentSubmitted = false;

                $scope.okModal = function (isValid) {
                  if (isValid) {
                    $modalInstance.close($scope);
                  } else {
                    $scope.commentSubmitted = true;
                  }
                };

                $scope.cancelModal = function () {
                  $modalInstance.dismiss('canceled');
                };

                $scope.updateCommentPM = function () {
                  if ($scope.comment.protective_marking.classification !== undefined) {

                    $scope.comment.protective_marking.classification_short = $scope.pm.classifications[$scope.selectCommentClassification].abbreviation;
                    $scope.comment.protective_marking.classification = $scope.pm.classifications[$scope.selectCommentClassification].classification;
                    $scope.comment.protective_marking.classification_rank = $scope.pm.classifications[$scope.selectCommentClassification].rank;

                    // National caveats
                    if ($scope.comment.protective_marking.national_caveats_primary_name !== undefined && $scope.comment.protective_marking.national_caveats_primary_name !== null) {
                      $scope.comment.protective_marking.national_caveats_members = $scope.pm.national_caveats[$scope.comment.protective_marking.national_caveats_primary_name].member_countries;
                      $scope.comment.protective_marking.national_caveats_rank = $scope.pm.national_caveats[$scope.comment.protective_marking.national_caveats_primary_name].rank;
                    }

                    // Codewords
                    if ($scope.comment.protective_marking.codewords !== undefined) {
                      $scope.comment.protective_marking.codewords_short = [];
                      angular.forEach($scope.comment.protective_marking.codewords, function (cw, key) {
                        $scope.comment.protective_marking.codewords_short.push($scope.pm.codewords[cw].abbreviation)
                      });
                    }
                  }
                };

              }
            });

          commentModal.result.then(function ($scope) {

            if ($scope.comment.type === 'comment' || ($scope.comment.type !== 'comment' && $scope.comment.body !== undefined)) {
              var commentData = {
                "type" : $scope.comment.type,
                "title" : $scope.comment.title,
                "body" : $scope.comment.body,
                "protective_marking" : {
                  "classification" : $scope.pm.classifications[$scope.selectCommentClassification].classification,
                  "classification_short" : $scope.pm.classifications[$scope.selectCommentClassification].abbreviation,
                  "classification_rank" : $scope.pm.classifications[$scope.selectCommentClassification].rank,
                  "codewords" : $scope.comment.protective_marking.codewords,
                  "codewords_short" : $scope.comment.protective_marking.codewords_short,
                  "national_caveats_primary_name" : $scope.comment.protective_marking.national_caveats_primary_name,
                  "national_caveats_members" : $scope.comment.protective_marking.national_caveats_members,
                  "national_caveats_rank" : $scope.comment.protective_marking.national_caveats_rank,
                  "descriptor" : $scope.comment.protective_marking.descriptor
                }
              };
            }

            var submittedComment = Comment.edit($scope.comment.resource_uri, commentData);

            submittedComment.success(function (data, status, headers, config) {
              $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
              $route.reload();
            });

          });

        });

      }
    }
  ]);

  
/************************************************************************
 *  ProjectsViewCtrl
 *    used by: ../projects/view , view-all  , view-latest, view-popular
 *
 *************************************************************************/
ideaworks.ngControllers.controller('ProjectsViewCtrl', ['$rootScope', '$scope', '$routeParams', '$location', '$route', '$modal', '$filter', 'User', 'Projects', 'Tags', 'Comment',
    function ($rootScope, $scope, $routeParams, $location, $route, $modal, $filter, User, Projects, Tags, Comment) {

      // set the currentContext
      $rootScope.currentContext = "projects";

      // get the list of published tags
      $scope.tags = Tags.get({
          status : 'published'
        });

      $scope.tagFilterType = 'multiple';

      $scope.setTagFilterType = function (type) {
        $scope.tagFilterType = type;
      }

      // include shared functions and services from Comment in services.js
      $scope.comment = Comment;

      // get the view path, type and layout from the URL
      $scope.viewPath = $location.path().slice(0, $location.path().lastIndexOf('/'));
      $scope.viewName = $scope.viewPath.split('/').pop();
      $scope.viewLayout = $location.path().split('/').pop();
      $scope.viewParams = $location.url().split('?')[1] ? '/?' + $location.url().split('?')[1] : '';

      // number of latest/most popular projects to show
      $scope.viewLatestCount = 5;

      // default view count
      $scope.viewDefaultCount = 20;

      // default view sort order
      $scope.viewDefaultOrderBy = '-created';

      // default view status
      $scope.viewDefaultStatus = 'published';
      $scope.status = $routeParams.status ? $routeParams.status : $scope.viewDefaultStatus;
      $scope.status = $routeParams.status__in ? 'all' : $scope.status;

      // default user filter
      $scope.viewDefaultUser = null;
      $scope.viewCurrentUser = $routeParams.user ? $routeParams.user : $scope.viewDefaultUser;

      $scope.viewIsLoading = true;

      $scope.doViewLoaded = function () {
        $scope.viewIsLoading = false;
      };

      // default view params, use values in query-string, otherwise use default values
      var viewParams = {
        limit : $routeParams.limit ? $routeParams.limit : $scope.viewDefaultCount, // number of records to load
        offset : $routeParams.offset ? $routeParams.offset : 0, // start point (for paging)
        order_by : $routeParams.order_by ? $routeParams.order_by : $scope.viewDefaultOrderBy, // sort order
        status : $routeParams.status ? $routeParams.status : $scope.viewDefaultStatus, // status
        user : $routeParams.user ? $routeParams.user : $scope.viewDefaultUser // user
      };
      $rootScope.currentView = $scope.viewName + '-' + viewParams.status;

      if ($routeParams.status === 'all' || $routeParams.status__in) {
        delete(viewParams.status);
      }

      if ($routeParams.status__in) {
        viewParams.status__in = $routeParams.status__in;
      }

      if ($routeParams.tags__in) {
        viewParams.tags__in = $routeParams.tags__in;
      }

      // if $scope.viewName is view-latest (and no limit in URL) then show latest $scope.viewLatestCount projects
      if ($scope.viewName === 'view-latest') {
        viewParams.limit = $routeParams.limit ? $routeParams.limit : $scope.viewLatestCount;
        $scope.orderProp = '-created';
      }

      // if $scope.viewName is view-all (and no limit in URL) then show all
      if ($scope.viewName === 'view-all') {
        viewParams.limit = $routeParams.limit ? $routeParams.limit : 0;
        $scope.orderProp = '-created';
      }

      // if $scope.viewName is view-popular then sort by back_count
      if ($scope.viewName === 'view-popular') {
        viewParams.limit = $routeParams.limit ? $routeParams.limit : $scope.viewLatestCount;
        viewParams.order_by = '-back_count';
        $scope.orderProp = '-back_count';
      }

      Projects.get(viewParams, function (data) {

        if (data.meta.total_count === 0) {
          $scope.doViewLoaded();
          $('.view-body').html('<div class="alert alert-danger"><strong>No projects found</strong><p>Please select another view.</p></div>');
        } else {
          // get maximum protective marking
          $scope.max_pm = data.meta.max_pm;
          $scope.projectsData = data;
          $scope.projectsCount = data.meta.total_count;
          if ($scope.viewLatestCount > $scope.projectsCount) {
            $scope.projectsDisplayCount = $scope.projectsCount
          } else {
            $scope.projectsDisplayCount = $scope.viewLatestCount;
          }
          $scope.projects = [];
          $scope.projectsList = [];

          angular.forEach(data.objects, function (project, key) {
            // calculate the like/dislike percentages for use in the likeBar visualisation
            project.like_percent = Math.round((project.like_count / (project.like_count + project.dislike_count) * 100));
            project.dislike_percent = 100 - project.like_percent;

            project.tag_list = project.tags.join(', ');

            if (project.contributor_name === ' ') {
              project.contributor_name = "Admin"
            }

            $scope.projects.push(project);

            // separate copy for list view (needed for filtering)
            $scope.projectsList = $scope.projects;

          });
        }
      });

      // filter clearing
      $scope.clearProjectsFilter = function () {
        $scope.filterOptions.filterText = '';
      };

      $scope.clearProjectsListFilter = function () {
        $scope.filterList = '';
      };

      $scope.clearTagsFilter = function () {
        $scope.tags.filterText = '';
      };

      
      /*********** ng-grid stuff ***********/

      // Make the title click-able and open the project in read mode
      var title_cellTemplate = '<div class="ngCellText" ng-class="col.colIndex()"><a ng-href="" ng-click="clickRow(row)"><span ng-cell-text>{{row.getProperty(col.field)}}</span></a></div>';

      // use created value (for correct sorting) but display the informal_created value
      var created_cellTemplate = '<div class="ngCellText" ng-class="col.colIndex()"><span ng-cell-text>{{row.entity.informal_created}}</span></div>';

      // display thumbs up for likes header
      var like_HeaderCellTemplate = '<div class="ngHeaderSortColumn {{col.headerClass}}" ng-style="{\'cursor\': col.cursor}" ng-class="{ \'ngSorted\': !noSortVisible }"><div ng-click="col.sort($event)" ng-class="\'colt\' + col.index" class="ngHeaderText"><i class="icon-thumbs-up icon-white like"></i></div><div class="ngSortButtonDown" ng-show="col.showSortButtonDown()"></div><div class="ngSortButtonUp" ng-show="col.showSortButtonUp()"></div><div class="ngSortPriority">{{col.sortPriority}}</div><div ng-class="{ ngPinnedIcon: col.pinned, ngUnPinnedIcon: !col.pinned }" ng-click="togglePin(col)" ng-show="col.pinnable"></div></div><div ng-show="col.resizable" class="ngHeaderGrip" ng-click="col.gripClick($event)" ng-mousedown="col.gripOnMouseDown($event)"></div>';

      // display thumbs down for dislikes header
      var dislike_HeaderCellTemplate = '<div class="ngHeaderSortColumn {{col.headerClass}}" ng-style="{\'cursor\': col.cursor}" ng-class="{ \'ngSorted\': !noSortVisible }"><div ng-click="col.sort($event)" ng-class="\'colt\' + col.index" class="ngHeaderText"><i class="icon-thumbs-down icon-white dislike"></i></div><div class="ngSortButtonDown" ng-show="col.showSortButtonDown()"></div><div class="ngSortButtonUp" ng-show="col.showSortButtonUp()"></div><div class="ngSortPriority">{{col.sortPriority}}</div><div ng-class="{ ngPinnedIcon: col.pinned, ngUnPinnedIcon: !col.pinned }" ng-click="togglePin(col)" ng-show="col.pinnable"></div></div><div ng-show="col.resizable" class="ngHeaderGrip" ng-click="col.gripClick($event)" ng-mousedown="col.gripOnMouseDown($event)"></div>';

      // display speech bubble for comments header
      var comment_HeaderCellTemplate = '<div class="ngHeaderSortColumn {{col.headerClass}}" ng-style="{\'cursor\': col.cursor}" ng-class="{ \'ngSorted\': !noSortVisible }"><div ng-click="col.sort($event)" ng-class="\'colt\' + col.index" class="ngHeaderText"><i class="icon-comment"></i></div><div class="ngSortButtonDown" ng-show="col.showSortButtonDown()"></div><div class="ngSortButtonUp" ng-show="col.showSortButtonUp()"></div><div class="ngSortPriority">{{col.sortPriority}}</div><div ng-class="{ ngPinnedIcon: col.pinned, ngUnPinnedIcon: !col.pinned }" ng-click="togglePin(col)" ng-show="col.pinnable"></div></div><div ng-show="col.resizable" class="ngHeaderGrip" ng-click="col.gripClick($event)" ng-mousedown="col.gripOnMouseDown($event)"></div>';

      // filter / search the list view
      $scope.$watch('filterList', function () {
        $scope.projectsList = $filter('filter')($scope.projects, $scope.filterList);
      });

      $scope.gridOptions = {
        data : 'projectsList',
        enableRowSelection : false,
        columnDefs : [{
            field : 'id',
            visible : false
          }, // just for linking , not displayed
          {
            field : 'title',
            displayName : 'Project title',
            width : '*******',
            cellTemplate : title_cellTemplate
          }, {
            field : 'created',
            displayName : 'Created',
            width : '***',
            cellTemplate : created_cellTemplate
          }, {
            field : 'title',
            displayName : 'By',
            width : '***'
          }, {
            field : 'tag_list',
            displayName : 'Tags',
            width : '***'
          }, {
            field : 'pretty_pm',
            displayName : 'Classification',
            width : '****'
          }, {
            field : 'like_count',
            width : '40px',
            headerCellTemplate : like_HeaderCellTemplate
          }, {
            field : 'dislike_count',
            width : '40px',
            headerCellTemplate : dislike_HeaderCellTemplate
          }, {
            field : 'comment_count',
            width : '40px',
            headerCellTemplate : comment_HeaderCellTemplate
          }
        ]
      };

      $scope.clickRow = function (row) {
        $scope.openProject(row.entity.id);
      }

      $scope.sortList = function (sort) {
        $scope.gridOptions.sortBy(sort);
      };

      $scope.$on('ngGridEventData', function (e, s) {
        if ($scope.projects !== undefined) {
          $scope.doViewLoaded();
        }
      });

      $scope.switchView = function () {
        $('.view-body').html('');
        $scope.filterByTag('');
      }

      $scope.openProject = function (id) {
        $scope.setPreviousViewUrl();
        $location.url('/projects/' + id + '/read');
      }

    }
  ]);

  
/************************************************************************
 *  ProjectCreateCtrl
 *    used by: ../projects/create
 *    Handles new project form
 *************************************************************************/
ideaworks.ngControllers.controller('ProjectCreateCtrl', ['$scope', '$routeParams', '$location', '$window', '$filter', '$cacheFactory', 'orderByFilter', '$compile', 'Project', 'Ideas', 'Tags',
    function ($scope, $routeParams, $location, $window, $filter, $cacheFactory, orderByFilter, $compile, Project, Ideas, Tags) {

      if ($routeParams.projectId === undefined) {
        $scope.mode = 'create';
      } else {
        $scope.mode = 'edit';
      }

      // create a blank project obj
      $scope.project = {};
      $scope.project.taglist = '';

      // get ideas list

      $scope.listIdeas = function () {
        var viewParams = {
          limit : 0, // number of records to load
          status : 'published', // status
          data_level : 'less',
          order_by : '-created' // sort order
        };

        Ideas.get(viewParams, function (data) {
          if (data.meta.total_count === 0) {
          } else {
            $scope.ideasCount = data.meta.total_count;
            $scope.ideasPickList = [];

            angular.forEach(data.objects, function (idea, key) {
              $scope.ideasPickList.push(idea);
            });

          }
        });
      }

      if ($scope.mode === 'edit') {

        Project.get($routeParams.projectId).success(function (project) {
          // get maximum protective marking
          $scope.max_pm = project.meta.max_pm;
          // get project data
          $scope.project = project.objects[0];
          $scope.selectClassification = $scope.project.protective_marking.classification_short;
          $scope.project.taglist = $scope.project.tags.join();

          if ($scope.project.status === 'hidden') {
            $scope.hideProject = true;
          }

        });

      } else {
        // its a new project (create);
        $scope.project.status = 'new unsaved';
        // create a blank obj for selected tags
        $scope.project.tags = [];
        $scope.project.protective_marking = {};
      }

      $scope.listIdeas();

      // check if value is in array
      $scope.isTagInArray = function (tag) {
        if ($scope.project.taglist !== undefined) {
          return $.inArray(tag, $scope.project.taglist.split(',')) > -1;
        } else {
          return false
        }
      }

      $scope.project.submitted = false;

      $scope.updatePM = function () {

        // add the abbreviated classification and rank
        $scope.project.classification_short = $scope.pm.classifications[$scope.selectClassification].abbreviation;
        $scope.project.protective_marking.classification_short = $scope.pm.classifications[$scope.selectClassification].abbreviation;
        $scope.project.protective_marking.classification = $scope.pm.classifications[$scope.selectClassification].classification;
        $scope.project.protective_marking.classification_rank = $scope.pm.classifications[$scope.selectClassification].rank;

        // National caveats
        if ($scope.project.protective_marking.national_caveats_primary_name !== undefined) {
          $scope.project.protective_marking.national_caveats_members = $scope.pm.national_caveats[$scope.project.protective_marking.national_caveats_primary_name].member_countries;
          $scope.project.protective_marking.national_caveats_rank = $scope.pm.national_caveats[$scope.project.protective_marking.national_caveats_primary_name].rank;
        }

        // Codewords
        if ($scope.project.protective_marking.codewords !== undefined) {
          $scope.project.protective_marking.codewords_short = [];
          angular.forEach($scope.project.protective_marking.codewords, function (cw, key) {
            $scope.project.protective_marking.codewords_short.push($scope.pm.codewords[cw].abbreviation)
          });
        }

      }

      $scope.showPMOptions = function () {
        $('#showMorePM').hide();
        $('#hideMorePM').show();
        $('#pm-options').fadeIn();
      }

      $scope.hidePMOptions = function () {
        $('#showMorePM').show();
        $('#hideMorePM').hide();
        $('#pm-options').fadeOut();
      }

      // get the list of available tags (will return draft and published tags);
      $scope.tags = Tags.get({
          status : 'draft,published,hidden'
        });

      // submit project
      $scope.submitProject = function (isValid, status) {
        $scope.project.submitted = true;
        $scope.project.status = status;

        if (!isValid) {
          return false;
        }

        // delete project.taglist and project.submitted, we don't need these now, were just for form display and validation purposes
        delete($scope.project.taglist);
        delete($scope.project.submitted);

        var submittedProject = Project.create($scope.project);
        submittedProject.success(function (data, status, headers, config) {
          var projectId = headers().location.split('/project')[1];
          // open the new project in read mode
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $location.url('/projects' + projectId + 'read');
        });
      };

      // save edited project
      $scope.saveProject = function (isValid, status) {
        $scope.project.submitted = true;
        $scope.project.status = status;

        if (!isValid) {
          return false;
        }

        // delete project.taglist and project.submitted, we don't need these now, were just for form display and validation purposes
        delete($scope.project.taglist);
        delete($scope.project.submitted);

        var submittedProject = Project.edit($scope.project);
        submittedProject.success(function (data, status, headers, config) {
          // re-open in read mode
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $location.url('/projects/' + $scope.project.id + '/read');
        });
      };

      $scope.cancelProject = function () {
        $scope.openPreviousViewUrl();
      }

      $scope.hiddenProject = function () {
        var data = {
          'status' : 'hidden'
        };
        Project.patch($routeParams.projectId, data).success(function (resp) {
          $scope.openPreviousViewUrl();
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $route.reload();
        });
      }

      // add / remove a selected tag
      $scope.addTag = function ($event) {

        // get a handle on the clicked tag button <a> element
        var $tag = $($event.target);

        // toggle the colour of the button
        if ($tag.hasClass('new-tag')) {
          $tag.toggleClass('btn-success');
        } else {
          $tag.toggleClass('btn-info');
        }
        // get the tag text value
        var tag = $tag.text().replace(/[0-9]/g, "").trim();
        // loop thru current selected tags, if tag clicked is already selected then remove it
        // otherwise add it
        var hasTag = $.inArray(tag, $scope.project.tags);

        if (hasTag === -1) {
          $scope.project.tags.push(tag);
        } else {
          $scope.project.tags.splice(hasTag, 1);
        }

        $scope.project.taglist = tag;
        if ($scope.project.taglist.length == 0) {
          $scope.project.taglist = '';
        } else {
          $scope.project.taglist = $scope.project.tags.join();
        }
      };

      $scope.clearFilter = function () {
        $scope.taglistfilter = '';
      };

      $scope.addNewTag = function () {

        if ($scope.taglistfilter === undefined || $scope.taglistfilter.length === 0) {
          return false
        }

        if ($scope.isExistingTag()) {
          $('.tagExistsAlert').fadeIn();
          setTimeout("$('.tagExistsAlert').fadeOut();", 2500);
        } else {
          $('span.tags').prepend($compile('<a class="btn btn-mini btn-tag btn-success new-tag disabled" ng-click="addTag($event)" ng-href="" ng-class="{\'btn-info\':isTagInArray(tag.text)}">' + $scope.taglistfilter + '</a>')($scope));
          $scope.clearFilter();
          setTimeout("$('.tags a')[0].click();", 500);
        }

      }

      // checks for existing tag
      $scope.isExistingTag = function () {
        if ($scope.taglistfilter !== undefined) {
          var newTag = $scope.taglistfilter,
          isExisting = false;
          angular.forEach($scope.tags.objects, function (tag, key) {
            if (newTag == tag.text) {
              isExisting = true;
            }
          });
          return isExisting;
        } else {
          return false
        }
      }

      $scope.sortTags = function (sortOpt) {
        $scope.orderProp = sortOpt;
      }

      // if a new project then create a related ideas array
      if ($scope.mode === 'create') {
        $scope.project.related_ideas = [];
      }

      // add / remove a selected tag
      $scope.selectIdea = function ($event) {

        // get a handle on the clicked idea <a> element
        var $idea = $($event.target);

        // toggle the tick
        $idea.toggleClass('icon-ok');
        $idea.parent().toggleClass('ichecked');
        $idea.parent().toggleClass('WOW');

        // get the tag text value
        var ideaId = $idea.attr('id')

          // loop thru current selected ideas, if idea clicked is already selected then remove it
          // otherwise add it
          var alreadySelected = $.inArray(ideaId, $scope.project.related_ideas);

        if (alreadySelected === -1) {
          $scope.project.related_ideas.push(ideaId);
        } else {
          $scope.project.related_ideas.splice(alreadySelected, 1);
        }


      };

      // check if value is in array
      $scope.isIdeaSelected = function (ideaId) {
        if ($scope.project.related_ideas !== undefined) {
          return $.inArray(ideaId, $scope.project.related_ideas) > -1;
        } else {
          return false
        }
      }

    }
  ]);

  
/************************************************************************
 *  ProjectReadCtrl
 *    used by: ../projects/:projectId and ../projects/:projectId/read
 *    Handles read version of project form
 *************************************************************************/
// This controller will handle IDEA READ FORM
ideaworks.ngControllers.controller('ProjectReadCtrl', ['$rootScope', '$scope', '$routeParams', '$route', '$location', '$window', '$cacheFactory', '$modal', 'Project', 'Ideas', 'Idea', 'Comment', 'Config', 'Backing',
    function ($rootScope, $scope, $routeParams, $route, $location, $window, $cacheFactory, $modal, Project, Ideas, Idea, Comment, Config, Backing) {

      // set the currentContext
      $rootScope.currentContext = "projects";

      $scope.backing = Backing;

      // remove your backing for this project
      $scope.removeBacking = function (uri) {
        $rootScope.deleteType = 'backing';
        Backing.del(uri).success(function (resp) {
          $rootScope.deleteType = '';
        });
      }

      $scope.openIdea = function (id) {
        $location.url('/ideas/' + id + '/read');
      }

      $scope.comment = Comment; // include shared functions and services from Comment in services.js

      Project.get($routeParams.projectId).success(function (project) {

        // get maximum protective marking
        $scope.max_pm = project.meta.max_pm;

        // get project data
        project = project.objects[0];

        $scope.project = project;
        $scope.project.related_ideasList = [];
        $.each(project.related_ideas, function (i, val) {

          Idea.getLess(val).success(function (idea) {

            $scope.project.related_ideasList.push(idea.objects[0]);
          });
        });

        if ($scope.project.user === $scope.user.id()) {
          $scope.user.isAuthor = true;
        } else {
          $scope.user.isAuthor = false;
        }

      });

      $scope.editProject = function () {
        $window.location.href = Config.frontEndPath + '/#/projects/' + $scope.project.id + '/edit'
      }

      $scope.closeProject = function (forceRefresh) {
        // if no history then just open the default view
        $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
        if ($window.history.length > 1) {
          $scope.openPreviousViewUrl(forceRefresh);
        } else {
          $window.location.href = Config.frontEndPath;
        }
      }

      $scope.confirmSoftDeleteProject = function () {
        $('.confirm-soft-delete-project').fadeIn();
        $('.popup-alert-mask').show();
      }

      $scope.confirmDeleteProject = function () {
        $('.confirm-delete-project').fadeIn();
        $('.popup-alert-mask').show();
      }

      $scope.softDeleteProject = function () {
        var data = {
          'status' : 'deleted'
        };
        Project.patch($routeParams.projectId, data).success(function (resp) {
          $scope.openPreviousViewUrl();
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $route.reload();
        });
      }

      $scope.deleteProject = function () {
        $rootScope.deleteType = 'project';
        Project.del($routeParams.projectId).success(function (resp) {
          $rootScope.deleteType = '';
        });
      }

      $scope.deleteComment = function (uri) {
        $rootScope.deleteType = 'comment';
        Comment.del(uri).success(function (resp) {
          $rootScope.deleteType = '';
        });
      }

      $scope.editComment = function (uri) {

        Comment.load(uri).success(function (resp) {
          $scope.commentData = resp;

          var commentModal = $modal.open({
              templateUrl : 'templates/modals/edit-comment.html',
              resolve : {
                cData : function () {
                  return $scope.commentData;
                },
                pm : function () {
                  return $scope.pm;
                }
              },
              controller : function ($scope, $modalInstance, cData, pm) {

                $scope.cData = cData;
                $scope.pm = pm;
                $scope.comment = cData.objects[0];
                $scope.selectCommentClassification = $scope.comment.protective_marking.classification_short;
                $scope.commentSubmitted = false;

                $scope.okModal = function (isValid) {
                  if (isValid) {
                    $modalInstance.close($scope);
                  } else {
                    $scope.commentSubmitted = true;
                  }
                };

                $scope.cancelModal = function () {
                  $modalInstance.dismiss('canceled');
                };

                $scope.updateCommentPM = function () {
                  if ($scope.comment.protective_marking.classification !== undefined) {

                    $scope.comment.protective_marking.classification_short = $scope.pm.classifications[$scope.selectCommentClassification].abbreviation;
                    $scope.comment.protective_marking.classification = $scope.pm.classifications[$scope.selectCommentClassification].classification;
                    $scope.comment.protective_marking.classification_rank = $scope.pm.classifications[$scope.selectCommentClassification].rank;

                    // National caveats
                    if ($scope.comment.protective_marking.national_caveats_primary_name !== undefined && $scope.comment.protective_marking.national_caveats_primary_name !== null) {
                      $scope.comment.protective_marking.national_caveats_members = $scope.pm.national_caveats[$scope.comment.protective_marking.national_caveats_primary_name].member_countries;
                      $scope.comment.protective_marking.national_caveats_rank = $scope.pm.national_caveats[$scope.comment.protective_marking.national_caveats_primary_name].rank;
                    }

                    // Codewords
                    if ($scope.comment.protective_marking.codewords !== undefined) {
                      $scope.comment.protective_marking.codewords_short = [];
                      angular.forEach($scope.comment.protective_marking.codewords, function (cw, key) {
                        $scope.comment.protective_marking.codewords_short.push($scope.pm.codewords[cw].abbreviation)
                      });
                    }
                  }
                };

              }
            });

          commentModal.result.then(function ($scope) {

            if ($scope.comment.type === 'comment' || ($scope.comment.type !== 'comment' && $scope.comment.body !== undefined) || $scope.comment.type === 'backing') {
              var commentData = {
                "type" : $scope.comment.type,
                "title" : $scope.comment.title,
                "body" : $scope.comment.body,
                "protective_marking" : {
                  "classification" : $scope.pm.classifications[$scope.selectCommentClassification].classification,
                  "classification_short" : $scope.pm.classifications[$scope.selectCommentClassification].abbreviation,
                  "classification_rank" : $scope.pm.classifications[$scope.selectCommentClassification].rank,
                  "codewords" : $scope.comment.protective_marking.codewords,
                  "codewords_short" : $scope.comment.protective_marking.codewords_short,
                  "national_caveats_primary_name" : $scope.comment.protective_marking.national_caveats_primary_name,
                  "national_caveats_members" : $scope.comment.protective_marking.national_caveats_members,
                  "national_caveats_rank" : $scope.comment.protective_marking.national_caveats_rank,
                  "descriptor" : $scope.comment.protective_marking.descriptor
                }
              };
            }

            var submittedComment = Comment.edit($scope.comment.resource_uri, commentData);

            submittedComment.success(function (data, status, headers, config) {
              $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
              $route.reload();
            });

          });

        });

      }
    }
  ]);

  
/************************************************************************
 *  TagsCtrl
 *    used by: ../tags/
 *    Utility to list out all available tags
 *************************************************************************/
ideaworks.ngControllers.controller('TagsCtrl', ['$scope', 'Tags',
    function ($scope, Tags) {
      $scope.tag = 'wow';
      $scope.tags = Tags.get();
      $scope.openTag = function (tag) {
        alert('Open view filtered by ' + tag)
      };
      $scope.clearFilter = function () {
        $scope.query = '';
      };
      $scope.addNewTag = function () {
        Tags.create({
          'text' : 'aaa000'
        });

      };
    }
  ]);

  
/************************************************************************
 *  loggedOutCtrl
 *    used by: ../logged-out/
 *    logged out page with login button
 *************************************************************************/
ideaworks.ngControllers.controller('loggedOutCtrl', ['$scope', '$window', '$location', 'Config',
    function ($scope, $window, $location, Config) {
      $scope.login = function () {
        $window.location.href = Config.appPath + '/accounts/login/?next=' + $location.protocol() + '://' + $location.host() + Config.frontEndPath;
      }
    }
  ]);

  
/************************************************************************
 *  ContentCreateCtrl
 *    used by: ../content/create
 *    Handles new content form
 *************************************************************************/
ideaworks.ngControllers.controller('ContentCreateCtrl', ['$scope', '$routeParams', '$location', '$window', '$filter', '$cacheFactory', 'orderByFilter', '$compile', 'Content',
    function ($scope, $routeParams, $location, $window, $filter, $cacheFactory, orderByFilter, $compile, Content) {
     
     // wait until the site content types promise has resolved (data loaded) or the code below could error
      $scope.getTypesPromise.then(function () {

        // create a blank content obj
        $scope.content = {};

        if ($routeParams.contentId === undefined) {
          $scope.mode = 'create';
        } else {
          $scope.mode = 'edit';
        }

        if ($scope.mode === 'edit') {

          Content.get($routeParams.contentId).success(function (content) {
            // get content data
            $scope.content = content.objects[0];
            $scope.selectClassification = $scope.content.protective_marking.classification_short;
            $scope.content.label = $scope.siteContentTypes[$scope.content.type].label;

            if ($scope.content.status === 'hidden') {
              $scope.hideContent = true;
            }

          });

        } else {

          if ($scope.siteContentTypes[$routeParams.contentType] !== undefined) {
            $scope.content.type = $routeParams.contentType;
            $scope.content.label = $scope.siteContentTypes[$routeParams.contentType].label;
          } else {
            $('.invalid-contenttype').fadeIn();
            $('.popup-alert-mask').show();
            return false;
          };

          // its a new content page (create);
          $scope.content.status = 'new unsaved';

          $scope.content.protective_marking = {};
        }

        $scope.content.submitted = false;

        $scope.updatePM = function () {

          // add the abbreviated classification and rank
          $scope.content.classification_short = $scope.pm.classifications[$scope.selectClassification].abbreviation;
          $scope.content.protective_marking.classification_short = $scope.pm.classifications[$scope.selectClassification].abbreviation;
          $scope.content.protective_marking.classification = $scope.pm.classifications[$scope.selectClassification].classification;
          $scope.content.protective_marking.classification_rank = $scope.pm.classifications[$scope.selectClassification].rank;

          // National caveats
          if ($scope.content.protective_marking.national_caveats_primary_name !== undefined) {
            $scope.content.protective_marking.national_caveats_members = $scope.pm.national_caveats[$scope.content.protective_marking.national_caveats_primary_name].member_countries;
            $scope.content.protective_marking.national_caveats_rank = $scope.pm.national_caveats[$scope.content.protective_marking.national_caveats_primary_name].rank;
          }

          // Codewords
          if ($scope.content.protective_marking.codewords !== undefined) {
            $scope.content.protective_marking.codewords_short = [];
            angular.forEach($scope.content.protective_marking.codewords, function (cw, key) {
              $scope.content.protective_marking.codewords_short.push($scope.pm.codewords[cw].abbreviation)
            });
          }

        }

        $scope.showPMOptions = function () {
          $('#showMorePM').hide();
          $('#hideMorePM').show();
          $('#pm-options').fadeIn();
        }

        $scope.hidePMOptions = function () {
          $('#showMorePM').show();
          $('#hideMorePM').hide();
          $('#pm-options').fadeOut();
        }

        // submit content
        $scope.submitContent = function (isValid, status) {
          $scope.content.submitted = true;
          $scope.content.status = status;

          if (!isValid) {
            return false;
          }

          // delete content.submitted
          delete($scope.content.submitted);
          delete($scope.content.label);

          var submittedContent = Content.create($scope.content);
          submittedContent.success(function (data, status, headers, config) {
            var contentId = headers().location.split('/content')[1];
            // open the new content in read mode
            $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
            $location.url('/contents' + contentId + 'read');
          });
        };

        // save edited content
        $scope.saveContent = function (isValid, status) {
          $scope.content.submitted = true;
          $scope.content.status = status;

          if (!isValid) {
            return false;
          }

          // delete content.submitted
          delete($scope.content.submitted);

          var submittedContent = Content.edit($scope.content);
          submittedContent.success(function (data, status, headers, config) {
            // re-open in read mode
            $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
            $location.url('/content/' + $scope.content.id + '/read');
          });
        };

        $scope.cancelContent = function () {
          $scope.openPreviousViewUrl();
        }

      });

    }
  ]);
/************************************************************************
 *  ContentViewCtrl
 *    used by: ../content/view
 *
 *************************************************************************/
ideaworks.ngControllers.controller('ContentViewCtrl', ['$scope', '$routeParams', '$location', 'Contents',
    function ($scope, $routeParams, $location, Contents) {

      var viewParams = {
        limit : $routeParams.limit ? $routeParams.limit : $scope.viewDefaultCount, // number of records to load
        offset : $routeParams.offset ? $routeParams.offset : 0, // start point (for paging)
        order_by : $routeParams.order_by ? $routeParams.order_by : $scope.viewDefaultOrderBy, // sort order
        status : $routeParams.status ? $routeParams.status : $scope.viewDefaultStatus, // status
        user : $routeParams.user ? $routeParams.user : $scope.viewDefaultUser, // user
        type : $routeParams.type ? $routeParams.type : 'all' // type
      };
      if ($routeParams.type === 'all') {
        delete(viewParams.type);
      }
      Contents.get(viewParams, function (data) {
        if (data.meta.total_count === 0) {
          $('.view-body').html('<div class="alert alert-danger"><strong>No content found</strong><p>Please select another view.</p></div>');
        } else {

          $scope.siteContent = [];

          angular.forEach(data.objects, function (doc, key) {

            $scope.siteContent.push(doc);

          });
        }
      });

      $scope.openContent = function (id) {
        $scope.setPreviousViewUrl();
        $location.url('/content/' + id + '/read');
      }
    }
  ]);

/************************************************************************
 *  ContentReadCtrl
 *    used by: ../content/:contentId/read
 *    Handles read version of site content form
 *************************************************************************/
// This controller will handle Content READ FORM
ideaworks.ngControllers.controller('ContentReadCtrl', ['$rootScope', '$scope', '$routeParams', '$route', '$location', '$window', '$cacheFactory', '$modal', 'Content', 'Config',
    function ($rootScope, $scope, $routeParams, $route, $location, $window, $cacheFactory, $modal, Content, Config) {

      Content.get($routeParams.contentId).success(function (content) {
        // get content data
        content = content.objects[0];
        $scope.content = content;
      });

      $scope.editContent = function () {
        $window.location.href = Config.frontEndPath + '/#/content/' + $scope.content.id + '/edit'
      }

      $scope.closeContent = function (forceRefresh) {
        // if no history then just open the default view
        $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
        if ($window.history.length > 1) {
          $scope.openPreviousViewUrl(forceRefresh);
        } else {
          $window.location.href = Config.frontEndPath;
        }
      }

      $scope.confirmSoftDeleteContent = function () {
        $('.confirm-soft-delete-content').fadeIn();
        $('.popup-alert-mask').show();
      }

      $scope.confirmDeleteContent = function () {
        $('.confirm-delete-content').fadeIn();
        $('.popup-alert-mask').show();
      }

      $scope.softDeleteContent = function () {
        var data = {
          'status' : 'deleted'
        };
        Content.patch($routeParams.contentId, data).success(function (resp) {
          $scope.openPreviousViewUrl();
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $route.reload();
        });
      }

      $scope.deleteContent = function () {
        $rootScope.deleteType = 'content';
        Content.del($routeParams.contentId).success(function (resp) {
          $rootScope.deleteType = '';
        });
      }

    }
  ]);

/************************************************************************
 *  ContentIndexCtrl
 *    used by: ../[content.type]   e.g, ../homepage
 *    Redirects to the 'index' page of each content type
 *************************************************************************/
// This controller will open homepage, help page index etc...
ideaworks.ngControllers.controller('ContentIndexCtrl', ['$rootScope', '$scope', '$routeParams', '$route', '$location', '$window', '$cacheFactory', '$modal', 'Content', 'Contents', 'Config',
    function ($rootScope, $scope, $routeParams, $route, $location, $window, $cacheFactory, $modal, Content, Contents, Config) {

      var viewParams = {};
      viewParams.type = $routeParams.contentType;
      viewParams.index = 'true';

      $scope.indexPageFound = true;

      Contents.get(viewParams, function (data) {
        if (data.meta.total_count === 0) {
          $scope.contentlabel = $scope.siteContentTypes[viewParams.type].label;
          $scope.indexPageFound = false;
        } else {
          $location.url('/content/' + data.objects[0].id + '/read');
        }
      });
    }
  ]);

/************************************************************************
 *  FeedbackCreateCtrl
 *    used by: ../feedback/create
 *    Handles new feedback form
 *************************************************************************/
ideaworks.ngControllers.controller('FeedbackCreateCtrl', ['$scope', '$routeParams', '$location', '$window', '$filter', '$cacheFactory', 'orderByFilter', '$compile', 'Feedback',
    function ($scope, $routeParams, $location, $window, $filter, $cacheFactory, orderByFilter, $compile, Feedback) {

      // create a blank feedback obj
      $scope.feedback = {};

      $scope.feedback.type = 'feedback';
      $scope.feedback.public = true;

      if ($routeParams.feedbackId === undefined) {
        $scope.mode = 'create';
      } else {
        $scope.mode = 'edit';
      }

      if ($scope.mode === 'edit') {

        Feedback.get($routeParams.feedbackId).success(function (feedback) {
          // get feedback data
          $scope.feedback = feedback.objects[0];
          $scope.selectClassification = $scope.feedback.protective_marking.classification_short;

          if ($scope.feedback.status === 'hidden') {
            $scope.hideFeedback = true;
          }

        });

      } else {

        // its a new feedback page (create);
        $scope.feedback.status = 'new unsaved';

        $scope.feedback.protective_marking = {};
      }

      $scope.feedback.submitted = false;

      $scope.updatePM = function () {

        // add the abbreviated classification and rank
        $scope.feedback.classification_short = $scope.pm.classifications[$scope.selectClassification].abbreviation;
        $scope.feedback.protective_marking.classification_short = $scope.pm.classifications[$scope.selectClassification].abbreviation;
        $scope.feedback.protective_marking.classification = $scope.pm.classifications[$scope.selectClassification].classification;
        $scope.feedback.protective_marking.classification_rank = $scope.pm.classifications[$scope.selectClassification].rank;

        // National caveats
        if ($scope.feedback.protective_marking.national_caveats_primary_name !== undefined) {
          $scope.feedback.protective_marking.national_caveats_members = $scope.pm.national_caveats[$scope.feedback.protective_marking.national_caveats_primary_name].member_countries;
          $scope.feedback.protective_marking.national_caveats_rank = $scope.pm.national_caveats[$scope.feedback.protective_marking.national_caveats_primary_name].rank;
        }

        // Codewords
        if ($scope.feedback.protective_marking.codewords !== undefined) {
          $scope.feedback.protective_marking.codewords_short = [];
          angular.forEach($scope.feedback.protective_marking.codewords, function (cw, key) {
            $scope.feedback.protective_marking.codewords_short.push($scope.pm.codewords[cw].abbreviation)
          });
        }

      }

      $scope.showPMOptions = function () {
        $('#showMorePM').hide();
        $('#hideMorePM').show();
        $('#pm-options').fadeIn();
      }

      $scope.hidePMOptions = function () {
        $('#showMorePM').show();
        $('#hideMorePM').hide();
        $('#pm-options').fadeOut();
      }

      // submit feedback
      $scope.submitFeedback = function (isValid, status) {
        $scope.feedback.submitted = true;
        $scope.feedback.status = status;

        if (!isValid) {
          return false;
        }

        // delete feedback.submitted
        delete($scope.feedback.submitted);

        var submittedFeedback = Feedback.create($scope.feedback);
        submittedFeedback.success(function (data, status, headers, config) {
          var feedbackId = headers().location.split('/feedback')[1];
          // open the new feedback in read mode
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $location.url('/feedback' + feedbackId + 'read');
        });
      };

      // save edited feedback
      $scope.saveFeedback = function (isValid, status) {
        $scope.feedback.submitted = true;
        $scope.feedback.status = status;

        if (!isValid) {
          return false;
        }

        // delete feedback.submitted
        delete($scope.feedback.submitted);

        var submittedFeedback = Feedback.edit($scope.feedback);
        submittedFeedback.success(function (data, status, headers, config) {
          // re-open in read mode
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $location.url('/feedback/' + $scope.feedback.id + '/read');
        });
      };

      $scope.cancelFeedback = function () {
        $scope.openPreviousViewUrl();
      }

    }
  ]);

/************************************************************************
 *  FeedbackViewCtrl
 *    used by: ../feedback/view
 *
 *************************************************************************/
ideaworks.ngControllers.controller('FeedbackViewCtrl', ['$scope', '$routeParams', '$location', 'Feedbacks',
    function ($scope, $routeParams, $location, Feedbacks) {

      // get the view path, type and layout from the URL
      $scope.viewPath = $location.path().slice(0, $location.path().lastIndexOf('/'));
      $scope.viewName = $location.path().split('/').pop();

      // default view status
      $scope.viewDefaultStatus = 'published';
      $scope.status = $routeParams.status ? $routeParams.status : $scope.viewDefaultStatus;
      $scope.status = $routeParams.status ? 'all' : $scope.status;

      var viewParams = {
        limit : $routeParams.limit ? $routeParams.limit : $scope.viewDefaultCount, // number of records to load
        offset : $routeParams.offset ? $routeParams.offset : 0, // start point (for paging)
        order_by : $routeParams.order_by ? $routeParams.order_by : $scope.viewDefaultOrderBy, // sort order
        status : $routeParams.status ? $routeParams.status : $scope.viewDefaultStatus, // status
        user : $routeParams.user ? $routeParams.user : $scope.viewDefaultUser, // user
        public : $routeParams.public ? $routeParams.public : true // user
      };

      if ($routeParams.status === 'all') {
        delete(viewParams.status);
      }
      if ($routeParams.public === 'all') {
        delete(viewParams.public);
      }

      $scope.orderProp = '-created';

      Feedbacks.get(viewParams, function (data) {
        if (data.meta.total_count === 0) {
          $('.view-body').html('<div class="alert alert-danger"><strong>No feedback found</strong><p>Please select another view.</p></div>');
        } else {

          $scope.siteFeedback = [];

          angular.forEach(data.objects, function (doc, key) {

            $scope.siteFeedback.push(doc);

          });
        }
      });

      $scope.openFeedback = function (id) {
        $scope.setPreviousViewUrl();
        $location.url('/feedback/' + id + '/read');
      }
    }
  ]);

/************************************************************************
 *  FeedbackReadCtrl
 *    used by: ../feedback/:feedbackId/read
 *    Handles read version of site feedback form
 *************************************************************************/
// This controller will handle Feedback READ FORM
ideaworks.ngControllers.controller('FeedbackReadCtrl', ['$rootScope', '$scope', '$routeParams', '$route', '$location', '$window', '$cacheFactory', '$modal', 'Feedback', 'Config', 'Comment',
    function ($rootScope, $scope, $routeParams, $route, $location, $window, $cacheFactory, $modal, Feedback, Config, Comment) {
      $scope.comment = Comment; // include shared functions and services from Comment in services.js
      $scope.formType = "feedback";
      Feedback.get($routeParams.feedbackId).success(function (feedback) {
        // get feedback data
        feedback = feedback.objects[0];
        $scope.feedback = feedback;

        // set the isAuthor flag
        if ($scope.feedback.user === $scope.user.id()) {
          $scope.user.isAuthor = true;
        } else {
          $scope.user.isAuthor = false;
        }

      });

      $scope.editFeedback = function () {
        $window.location.href = Config.frontEndPath + '/#/feedback/' + $scope.feedback.id + '/edit'
      }

      $scope.closeFeedback = function (forceRefresh) {
        // if no history then just open the default view
        $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
        if ($window.history.length > 1) {
          $scope.openPreviousViewUrl(forceRefresh);
        } else {
          $window.location.href = Config.frontEndPath;
        }
      }

      $scope.confirmSoftDeleteFeedback = function () {
        $('.confirm-soft-delete-feedback').fadeIn();
        $('.popup-alert-mask').show();
      }

      $scope.confirmDeleteFeedback = function () {
        $('.confirm-delete-feedback').fadeIn();
        $('.popup-alert-mask').show();
      }

      $scope.softDeleteFeedback = function () {
        var data = {
          'status' : 'deleted'
        };
        Feedback.patch($routeParams.feedbackId, data).success(function (resp) {
          $scope.openPreviousViewUrl();
          $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
          $route.reload();
        });
      }

      $scope.deleteFeedback = function () {
        $rootScope.deleteType = 'feedback';
        Feedback.del($routeParams.feedbackId).success(function (resp) {
          $rootScope.deleteType = '';
        });
      }

      $scope.deleteComment = function (uri) {
        $rootScope.deleteType = 'comment';
        Comment.del(uri).success(function (resp) {
          $rootScope.deleteType = '';
        });
      }

      $scope.editComment = function (uri) {

        Comment.load(uri).success(function (resp) {
          $scope.commentData = resp;

          var commentModal = $modal.open({
              templateUrl : 'templates/modals/edit-comment.html',
              resolve : {
                cData : function () {
                  return $scope.commentData;
                },
                pm : function () {
                  return $scope.pm;
                }
              },
              controller : function ($scope, $modalInstance, cData, pm) {
                $scope.cData = cData;
                $scope.pm = pm;
                $scope.comment = cData.objects[0];
                $scope.selectCommentClassification = $scope.comment.protective_marking.classification_short;
                $scope.commentSubmitted = false;

                $scope.okModal = function (isValid) {
                  if (isValid) {
                    $modalInstance.close($scope);
                  } else {
                    $scope.commentSubmitted = true;
                  }
                };

                $scope.cancelModal = function () {
                  $modalInstance.dismiss('canceled');
                };

                $scope.updateCommentPM = function () {
                  if ($scope.comment.protective_marking.classification !== undefined) {

                    $scope.comment.protective_marking.classification_short = $scope.pm.classifications[$scope.selectCommentClassification].abbreviation;
                    $scope.comment.protective_marking.classification = $scope.pm.classifications[$scope.selectCommentClassification].classification;
                    $scope.comment.protective_marking.classification_rank = $scope.pm.classifications[$scope.selectCommentClassification].rank;

                    // National caveats
                    if ($scope.comment.protective_marking.national_caveats_primary_name !== undefined && $scope.comment.protective_marking.national_caveats_primary_name !== null) {
                      $scope.comment.protective_marking.national_caveats_members = $scope.pm.national_caveats[$scope.comment.protective_marking.national_caveats_primary_name].member_countries;
                      $scope.comment.protective_marking.national_caveats_rank = $scope.pm.national_caveats[$scope.comment.protective_marking.national_caveats_primary_name].rank;
                    }

                    // Codewords
                    if ($scope.comment.protective_marking.codewords !== undefined) {
                      $scope.comment.protective_marking.codewords_short = [];
                      angular.forEach($scope.comment.protective_marking.codewords, function (cw, key) {
                        $scope.comment.protective_marking.codewords_short.push($scope.pm.codewords[cw].abbreviation)
                      });
                    }
                  }
                };

              }
            });

          commentModal.result.then(function ($scope) {

            if ($scope.comment.type === 'comment' || ($scope.comment.type !== 'comment' && $scope.comment.body !== undefined)) {
              var commentData = {
                "type" : $scope.comment.type,
                "title" : $scope.comment.title,
                "body" : $scope.comment.body,
                "protective_marking" : {
                  "classification" : $scope.pm.classifications[$scope.selectCommentClassification].classification,
                  "classification_short" : $scope.pm.classifications[$scope.selectCommentClassification].abbreviation,
                  "classification_rank" : $scope.pm.classifications[$scope.selectCommentClassification].rank,
                  "codewords" : $scope.comment.protective_marking.codewords,
                  "codewords_short" : $scope.comment.protective_marking.codewords_short,
                  "national_caveats_primary_name" : $scope.comment.protective_marking.national_caveats_primary_name,
                  "national_caveats_members" : $scope.comment.protective_marking.national_caveats_members,
                  "national_caveats_rank" : $scope.comment.protective_marking.national_caveats_rank,
                  "descriptor" : $scope.comment.protective_marking.descriptor
                }
              };
            }

            var submittedComment = Comment.edit($scope.comment.resource_uri, commentData);

            submittedComment.success(function (data, status, headers, config) {
              $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
              $route.reload();
            });

          });

        });

      }

    }
  ]);