/* (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK */

'use strict';

/************************************************************************
 *  Services
 *    ideaworks.ngServices
 *************************************************************************/

ideaworks.ngServices = angular.module('ideaworks.ngServices', ['ngResource']);

ideaworks.ngServices.factory('Config', ['$http',
    function ($http) {
      var Config = {};

      // Change to suit host server
      Config.appProtocol = "http://";
      
      // Hostname. e.g. beta.myserver.com
      Config.appHost = "ideaworks";
      
      // Path to the API assuming it's hanging off a different path to the frontend. Eg. "/ideaworks_api";
      Config.appPath = "/ideaworks_api";
      
      // Path to frontend Eg. "/istarter";
      Config.frontEndPath = "";
      
      // Path to specific API, which gets appended to the appPath. Allows us to change to new API versions with ease.
      Config.apiPath = "/api/v1/";

      return Config;
    }
  ]);

/************************************************************************
 *  Idea
 *  .get(GET), .create (POST), .edit (PUT), .delete (DELETE) a single idea
 *************************************************************************/
ideaworks.ngServices.factory('Idea', ['$http', 'Config',
    function ($http, Config) {

      var Idea = {};

      Idea.get = function (id) {
        return $http.get(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'idea/' + id + '/');
      };

      Idea.getLess = function (id) {
        return $http.get(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'idea/' + id + '/?data_level=less');
      };

      Idea.create = function (ideaData) {
        return $http.post(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'idea/', ideaData);
      };

      Idea.edit = function (ideaData) {
        var id = ideaData.id;
        return $http.put(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'idea/' + id + '/', ideaData);
      };

      Idea.patch = function (id, ideaData) {
        return $http({
          method : 'PATCH',
          url : Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'idea/' + id + '/',
          data : ideaData
        });
      };

      Idea.del = function (id) {
        return $http({
          method : 'DELETE',
          url : Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'idea/' + id + '/'
        });
      };

      return Idea;
    }
  ]);

/************************************************************************
 *  Ideas
 *   Loads (GET) all ideas or ideas by limit/offset
 *************************************************************************/
ideaworks.ngServices.factory('Ideas', ['$resource', 'Config',
    function ($resource, Config) {

      return $resource(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'idea/', {}, {
        get : {
          method : 'GET',
          cache : true,
          params : {
            order_by : '-created',
            limit : '0',
            offset : '0',
            data_level : 'more'
          }
        }
      })
    }
  ]);

/************************************************************************
 *  Project
 *  .get(GET), .create (POST), .edit (PUT), .delete (DELETE) a single project
 *************************************************************************/
ideaworks.ngServices.factory('Project', ['$http', 'Config',
    function ($http, Config) {

      var Project = {};

      Project.get = function (id) {
        return $http.get(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'project/' + id + '/');
      };

      Project.create = function (projectData) {
        return $http.post(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'project/', projectData);
      };

      Project.edit = function (projectData) {
        var id = projectData.id;
        return $http.put(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'project/' + id + '/', projectData);
      };

      Project.patch = function (id, projectData) {
        return $http({
          method : 'PATCH',
          url : Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'project/' + id + '/',
          data : projectData
        });
      };

      Project.del = function (id) {
        return $http({
          method : 'DELETE',
          url : Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'project/' + id + '/'
        });
      };

      return Project;
    }
  ]);

/************************************************************************
 *  Projects
 *   Loads (GET) all projects or projects by limit/offset
 *************************************************************************/
ideaworks.ngServices.factory('Projects', ['$resource', 'Config',
    function ($resource, Config) {

      return $resource(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'project/', {}, {
        get : {
          method : 'GET',
          cache : true,
          params : {
            order_by : '-created',
            limit : '0',
            offset : '0',
            data_level : 'proj_more'
          }
        }
      })
    }
  ]);

/************************************************************************
 *  Tags
 *   Loads all tags
 *************************************************************************/
ideaworks.ngServices.factory('Tags', ['$resource', 'Config',
    function ($resource, Config) {
      return $resource(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'tag/', {}, {
        get : {
          method : 'GET',
          params : {
            limit : '0',
            offset : '0',
            status : ''
          }
        },
        create : {
          method : 'POST',
          params : {
            endPoint : "tag/"
          }
        }
      })
    }
  ]);

/************************************************************************
 *  Vote
 *  .create (POST), like dislike
 *************************************************************************/
ideaworks.ngServices.factory('Vote', ['$http', '$modal', '$route', '$cacheFactory', 'Config',
    function ($http, $modal, $route, $cacheFactory, Config) {
      var Vote = {};

      Vote.create = function (docId, voteData, voteType) { // voteType = likes or dislikes , voteData param is currently empty but here for completeness
        return $http.post(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'idea/' + docId + '/' + voteType + '/', voteData);
      };

      return Vote;

    }
  ]);

/************************************************************************
 *  Backing
 *  .create (POST), .remove (DELETE)
 *************************************************************************/
ideaworks.ngServices.factory('Backing', ['$http', '$modal', '$route', '$cacheFactory', 'Config',
    function ($http, $modal, $route, $cacheFactory, Config) {
      var Backing = {};

      Backing.create = function (docId, backingData) {
        return $http.post(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'project/' + docId + '/backs/', backingData);
      };

      Backing.remove = function (docId, backIndex) {
        return $http({
          method : 'DELETE',
          url : Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'project/' + docId + '/backs/' + backIndex
        });
      };

      Backing.del = function (uri) {
        return $http({
          method : 'DELETE',
          url : Config.appProtocol + Config.appHost + Config.appPath + uri
        });
      };

      return Backing;

    }
  ]);

/************************************************************************
 *  Comment
 *  .create (POST), add
 *************************************************************************/
/* ########## make this generic so that comments can be added to feedback as well as ideas */
ideaworks.ngServices.factory('Comment', ['$http', '$modal', '$route', '$cacheFactory', 'Config', 'Vote', 'Backing',
    function ($http, $modal, $route, $cacheFactory, Config, Vote, Backing) {
      var Comment = {};

      // Create [post] a new comment
      Comment.create = function (docId, commentData, docContext) {
        return $http.post(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + docContext + '/' + docId + '/comments/', commentData);
      };

      // Pop up modal and create a comment
      Comment.add = function (docId, type, pm, user, docContext) {
        // Stop if user is not logged in
        if (user.name() === 'Anonymous') {
          $('.anonymous-action').fadeIn();
          $('.popup-alert-mask').show();
          return false;
        }

        var commentModal = $modal.open({
            templateUrl : 'templates/modals/' + type + '.html',
            controller : function ($scope, $modalInstance, pm) {
              $scope.formType = docContext;
              $scope.pm = pm;
              $scope.comment = {};
              $scope.comment.protective_marking = {};
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
                if ($scope.selectCommentClassification !== undefined) {

                  // add the abbreviated classification and rank
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

            },
            resolve : {
              pm : function () {
                return pm
              }

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

          if ($scope.comment.type === 'like' || $scope.comment.type === 'dislike') {

            var submittedVote = Vote.create(docId, {}, $scope.comment.type + 's');

            submittedVote.success(function (data, status, headers, config) {
              if (status !== 201) {}
              else {

                if ($scope.comment.body !== undefined) {
                  var submittedComment = Comment.create(docId, commentData, docContext);

                  submittedComment.success(function (data, status, headers, config) {
                    $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
                    $route.reload();
                  });
                } else {
                  $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
                  $route.reload();
                }

              }

            });
          }

          // Project backing
          if ($scope.comment.type === 'backing') {

            var submittedBacking = Backing.create(docId, {});

            submittedBacking.success(function (data, status, headers, config) {
              if (status !== 201) {}
              else {

                if ($scope.comment.body !== undefined) {
                  var submittedComment = Comment.create(docId, commentData, docContext);

                  submittedComment.success(function (data, status, headers, config) {
                    $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
                    $route.reload();
                  });
                } else {
                  $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
                  $route.reload();
                }

              }

            });
          }

          if ($scope.comment.type === 'comment') {
            var submittedComment = Comment.create(docId, commentData, docContext);

            submittedComment.success(function (data, status, headers, config) {
              $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully
              $route.reload();
            });

          }

        });

      };

      Comment.del = function (uri) {
        return $http({
          method : 'DELETE',
          url : Config.appProtocol + Config.appHost + Config.appPath + uri
        });
      };

      Comment.load = function (uri) {
        return $http.get(Config.appProtocol + Config.appHost + Config.appPath + uri);

      };

      Comment.edit = function (uri, commentData) {
        return $http({
          method : 'PATCH',
          url : Config.appProtocol + Config.appHost + Config.appPath + uri,
          data : commentData
        });
      };

      return Comment;

    }
  ]);

/************************************************************************
 *  User
 *   TBC - this will plug into the user API
 *************************************************************************/

ideaworks.ngServices.factory('User', ['$http', '$modal', '$route', '$cacheFactory', 'Config',
    function ($http, $modal, $route, $cacheFactory, Config) {
      var User = {};

      User.loggedIn = function () {
        return true
      };
      User.id = '';
      User.name = function () {
        return 'Joe Bloggs';
      };
      // User.roles ='';
      // etc...
      return User;
    }
  ]);

/************************************************************************
 *  Protective Marking
 *
 *************************************************************************/

ideaworks.ngServices.factory('ProtectiveMarking', ['$http', 'Config',
    function ($http, Config) {

      var ProtectiveMarking = {};

      ProtectiveMarking.get = function (element) {
        // return $http.get(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'protective_marking/' + element + '.json', {
        return $http.get(Config.appProtocol + Config.appHost + Config.frontEndPath + '/data/protective_marking/' + element + '.json', {
          cache : true
        });
      };

      return ProtectiveMarking;
    }
  ]);

/************************************************************************
 *  Content
 *  .get(GET), .create (POST), .edit (PUT), .delete (DELETE) a single content page
 *************************************************************************/
ideaworks.ngServices.factory('Content', ['$http', 'Config',
    function ($http, Config) {

      var Content = {};
      Content.getTypes = function () {
        return $http.get(Config.appProtocol + Config.appHost + Config.frontEndPath + '/data/site_content/types.json', {
          cache : true
        });
      };
      Content.get = function (id) {
        return $http.get(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'site_content/' + id + '/');
      };

      Content.create = function (contentData) {
        return $http.post(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'site_content/', contentData);
      };

      Content.edit = function (contentData) {
        var id = contentData.id;
        return $http.put(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'site_content/' + id + '/', contentData);
      };

      Content.patch = function (id, contentData) {
        return $http({
          method : 'PATCH',
          url : Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'site_content/' + id + '/',
          data : contentData
        });
      };

      Content.del = function (id) {
        return $http({
          method : 'DELETE',
          url : Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'site_content/' + id + '/'
        });
      };

      return Content;
    }
  ]);

/************************************************************************
 *  Contents
 *   Loads (GET) all contents or contents by limit/offset
 *************************************************************************/
ideaworks.ngServices.factory('Contents', ['$resource', 'Config',
    function ($resource, Config) {

      return $resource(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'site_content/', {}, {
        get : {
          method : 'GET',
          cache : true,
          params : {
            order_by : '-created',
            limit : '0',
            offset : '0'
          }
        }
      })
    }
  ]);

/************************************************************************
 *  Feedback
 *  .get(GET), .create (POST), .edit (PUT), .delete (DELETE) a single feedback page
 *************************************************************************/
ideaworks.ngServices.factory('Feedback', ['$http', 'Config',
    function ($http, Config) {

      var Feedback = {};

      Feedback.get = function (id) {
        return $http.get(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'feedback/' + id + '/');
      };

      Feedback.create = function (feedbackData) {
        return $http.post(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'feedback/', feedbackData);
      };

      Feedback.edit = function (feedbackData) {
        var id = feedbackData.id;
        return $http.put(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'feedback/' + id + '/', feedbackData);
      };

      Feedback.patch = function (id, feedbackData) {
        return $http({
          method : 'PATCH',
          url : Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'feedback/' + id + '/',
          data : feedbackData
        });
      };

      Feedback.del = function (id) {
        return $http({
          method : 'DELETE',
          url : Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'feedback/' + id + '/'
        });
      };

      return Feedback;
    }
  ]);

/************************************************************************
 *  Feedbacks
 *   Loads (GET) all feedbacks or feedbacks by limit/offset
 *************************************************************************/
ideaworks.ngServices.factory('Feedbacks', ['$resource', 'Config',
    function ($resource, Config) {

      return $resource(Config.appProtocol + Config.appHost + Config.appPath + Config.apiPath + 'feedback/', {}, {
        get : {
          method : 'GET',
          cache : true,
          params : {
            order_by : '-created',
            limit : '0',
            offset : '0'
          }
        }
      })
    }
  ]);