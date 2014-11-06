/* (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK */

'use strict';

/************************************************************************
 *  ideaworks
 *     main namespace
 *************************************************************************/

var ideaworks = {};

/************************************************************************
 *  ideaworks.ngApp
 *     main Angular JS module
 *************************************************************************/

// create main angular module and state dependencies
ideaworks.ngApp = angular.module(
    // module name
    'ideaworks.ngApp',
    // module dependencies, go and include these modules...
    [
      'ngRoute',
      'ngGrid',
      'ngCookies',
      'ui.bootstrap',
      'textAngular',
      'ideaworks.ngServices',
      'ideaworks.ngAnimations',
      'ideaworks.ngControllers',
      'ideaworks.ngDirectives',
      'ideaworks.ngFilters'
    ]);

/************************************************************************
 *  Configuration
 *   For this module configure the router ($routeProvider) to handle all URLs,
 *   linking each to a VIEW (aka a HTML template) and a CONTROLLER
 *************************************************************************/
ideaworks.ngApp.config(['$routeProvider', '$resourceProvider',
    function ($routeProvider, $resourceProvider) {
      $routeProvider.

      /* Idea view routes */
      when('/ideas/view-all/:viewLayout', {
        templateUrl : function (params) {
          return 'templates/ideas/view/' + params.viewLayout + '.html';
        },
        controller : 'IdeasViewCtrl'
      }).

      when('/ideas/view-latest/:viewLayout', {
        templateUrl : function (params) {
          return 'templates/ideas/view/' + params.viewLayout + '.html';
        },
        controller : 'IdeasViewCtrl'
      }).

      when('/ideas/view-my/:viewLayout', {
        templateUrl : function (params) {
          return 'templates/ideas/view/' + params.viewLayout + '.html';
        },
        controller : 'IdeasViewCtrl'
      }).

      when('/ideas/view-popular/:viewLayout', {
        templateUrl : function (params) {
          return 'templates/ideas/view/' + params.viewLayout + '.html';
        },
        controller : 'IdeasViewCtrl'
      }).

      /* Idea CRUD routes */
      when('/ideas/create', {
        templateUrl : 'templates/ideas/create.html',
        controller : 'IdeaCreateCtrl'
      }).

      when('/ideas/:ideaId', {
        templateUrl : 'templates/ideas/read.html',
        controller : 'IdeaReadCtrl'
      }).

      when('/ideas/:ideaId/read', {
        templateUrl : 'templates/ideas/read.html',
        controller : 'IdeaReadCtrl'
      }).

      when('/ideas/:ideaId/edit', {
        templateUrl : 'templates/ideas/create.html',
        controller : 'IdeaCreateCtrl'
      }).

      when('/ideas/:ideaId/delete', {
        templateUrl : 'templates/ideas/delete.html',
        controller : 'IdeaDeleteCtrl'
      }).
      
 /* Project view routes */
      when('/projects/view-all/:viewLayout', {
        templateUrl : function (params) {
          return 'templates/projects/view/' + params.viewLayout + '.html';
        },
        controller : 'ProjectsViewCtrl'
      }).

      when('/projects/view-latest/:viewLayout', {
        templateUrl : function (params) {
          return 'templates/projects/view/' + params.viewLayout + '.html';
        },
        controller : 'ProjectsViewCtrl'
      }).

      when('/projects/view-my/:viewLayout', {
        templateUrl : function (params) {
          return 'templates/projects/view/' + params.viewLayout + '.html';
        },
        controller : 'ProjectsViewCtrl'
      }).

      when('/projects/view-popular/:viewLayout', {
        templateUrl : function (params) {
          return 'templates/projects/view/' + params.viewLayout + '.html';
        },
        controller : 'ProjectsViewCtrl'
      }).

      /* Project CRUD routes */
      when('/projects/create', {
        templateUrl : 'templates/projects/create.html',
        controller : 'ProjectCreateCtrl'
      }).

      when('/projects/:projectId', {
        templateUrl : 'templates/projects/read.html',
        controller : 'ProjectReadCtrl'
      }).

      when('/projects/:projectId/read', {
        templateUrl : 'templates/projects/read.html',
        controller : 'ProjectReadCtrl'
      }).

      when('/projects/:projectId/edit', {
        templateUrl : 'templates/projects/create.html',
        controller : 'ProjectCreateCtrl'
      }).

      when('/projects/:projectId/delete', {
        templateUrl : 'templates/projects/delete.html',
        controller : 'ProjectDeleteCtrl'
      }).

      /* Content view routes */
      when('/content/view', {
        templateUrl : 'templates/site-content/view.html',
        controller : 'ContentViewCtrl'
      }).

      /* Content CRUD routes */
      when('/content/create/:contentType', {
        templateUrl : 'templates/site-content/create.html',
        controller : 'ContentCreateCtrl'
      }).

      when('/content/:contentId/read', {
        templateUrl : 'templates/site-content/read.html',
        controller : 'ContentReadCtrl'
      }).

      when('/content/:contentId/edit', {
        templateUrl : 'templates/site-content/create.html',
        controller : 'ContentCreateCtrl'
      }).

      when('/content/:contentId/delete', {
        templateUrl : 'templates/site-content/delete.html',
        controller : 'ContentDeleteCtrl'
      }).

      /* Index page routes */
      when('/:contentType/index', {
        templateUrl : 'templates/site-content/index.html',
        controller : 'ContentIndexCtrl'
      }).

      /* Feedback view routes */
      when('/feedback/view-all', {
        templateUrl : 'templates/feedback/view.html',
        controller : 'FeedbackViewCtrl'
      }).
      
      when('/feedback/view-my', {
        templateUrl : 'templates/feedback/view.html',
        controller : 'FeedbackViewCtrl'
      }).
      
      when('/feedback/view-private', {
        templateUrl : 'templates/feedback/view.html',
        controller : 'FeedbackViewCtrl'
      }).      
      
      /* Feedback CRUD routes */
      when('/feedback/create', {
        templateUrl : 'templates/feedback/create.html',
        controller : 'FeedbackCreateCtrl'
      }).

      when('/feedback/:feedbackId/read', {
        templateUrl : 'templates/feedback/read.html',
        controller : 'FeedbackReadCtrl'
      }).

      when('/feedback/:feedbackId/edit', {
        templateUrl : 'templates/feedback/create.html',
        controller : 'FeedbackCreateCtrl'
      }).

      when('/feedback/:feedbackId/delete', {
        templateUrl : 'templates/feedback/delete.html',
        controller : 'FeedbackDeleteCtrl'
      }).

      /* Tag routes */
      when('/tags', {
        templateUrl : 'templates/tags.html',
        controller : 'TagsCtrl'
      }).

      /* Misc routes */
      when('/logged-out', {
        templateUrl : 'templates/logged-out.html',
        controller : 'loggedOutCtrl'
      }).

      when('/not-found', {
        templateUrl : 'templates/not-found.html'
      }).

      when('/docs/description-of-service', {
        templateUrl : 'templates/docs/description-of-service.html'
      }).

      when('/docs/about', {
        templateUrl : 'templates/docs/about.html'
      }).

      otherwise({
        redirectTo : '/ideas/view-latest/summary'
      });

      $resourceProvider.defaults.stripTrailingSlashes = false;
    }
  ]);

/************************************************************************
 * Response Interceptor
 *
 * Handles 401 errors for all api calls and redirects the user to
 * the logged out page. Also handles 204 (duplicate likes/dislikes)
 *************************************************************************/
ideaworks.ngApp.config(['$httpProvider', function ($httpProvider, $rootScope) {
      $httpProvider.interceptors.push(['$q', '$location', '$rootScope', '$cacheFactory', '$injector', function ($q, $location, $rootScope, $cacheFactory, $injector) {
            return {
              'response' : function (response) {

                if (response.status === 204) { // DELETE and duplicate responses

                  if (response.config.method === 'POST') {
                    // its a duplicate vote
                    $('.duplicate-vote').fadeIn();
                    $('.popup-alert-mask').show();
                  }

                  if (response.config.method === 'DELETE') {
                    // its a deletion
                    $cacheFactory.get('$http').removeAll(); // clear cache or the view/form may not refresh fully

                    if ($rootScope.deleteType === 'idea') {
                      $('.idea-deleted').fadeIn();
                      $('.popup-alert-mask').show();
                    }

                    if ($rootScope.deleteType === 'comment' || $rootScope.deleteType === 'backing' ) {
                      // can't include $route a a dependency here, so have to use $injection on the fly
                      var $route = $injector.get('$route');
                      // refresh the page
                      $route.reload();
                    }

                  }

                }

                return response || $q.when(response);
              },
              'responseError' : function (rejection) {
                if (rejection.status === 401) {
                  $location.path('/logged-out/');
                }
                if (rejection.status === 404) {
                  $location.path('/not-found/');
                }
                $rootScope.errorUrl = rejection.config.url;
                return $q.reject(rejection);
              }
            };
          }
        ]);

    }
  ]);

ideaworks.ngApp.config(['$httpProvider', function ($httpProvider) {
      $httpProvider.defaults.headers.patch = {
        'Content-Type' : 'application/json;charset=utf-8'
      }
    }
  ]);

/************************************************************************
 * Global runs
 *
 * Run this code for every controller/page etc
 *************************************************************************/
ideaworks.ngApp.run(function run() {});

/************************************************************************
 *  Run code when DOM loaded...
 *************************************************************************/
$(document).ready(
  function () {
  // stuff here....

});