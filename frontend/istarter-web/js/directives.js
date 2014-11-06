/* (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK */

'use strict';

/************************************************************************
 *  Directives
 *    ideaworks.ngDirectives
 *************************************************************************/

ideaworks.ngDirectives = angular.module('ideaworks.ngDirectives', []);

/************************************************************************
 *  ideaLikeBar
 *    creates the green/red bar to visualise the likes/dislikes per idea
 *    include with:
 *      <!-- directive: idea-likes-bar -->
 *      <idea-likes-bar></idea-likes-bar>
 *************************************************************************/
ideaworks.ngDirectives.directive('ideaLikesBar', function () {
  return {
    restrict : 'AEMC',
    replace : 'true',
    templateUrl : 'templates/ideas/likes-bar.html'
  };
});

/************************************************************************
 *  protectiveMarking
 *    creates the protective marking banner per idea
 *    include with:
 *      <protective-marking type=""></protective-marking>
 *      where type is full, compact, or text - defaults to full
 *************************************************************************/
ideaworks.ngDirectives.directive('protectiveMarking', function ($compile) {
  return {
    restrict : 'AEMC',
    replace : 'true',
    template : '<span></span>',
    link : function (scope, element, attrs) {
      var pm = scope.pm;

      /* !!! Lots of duplicated code here now, need to consolidate into a modular $watch, or call shared functions from within the $watch .....  !!! */

      // $watch: wait until the scope has propagated before accessing, and watch for any changes (for when used on a form)
      scope.$watch('idea', function (idea) {
       
        if (idea !== undefined) {
          if (idea.classification_short !== undefined) {
            // if no classification selected or available then just quit...
            if (idea.classification_short === '') {
              return false;
            };

            var cs = idea.classification_short.toUpperCase();
            // !! look this up now from the PM api
            var classification = pm.classifications[cs].classification.toUpperCase();
            var className = pm.classifications[cs].class_name;
            var css = 'style="' + pm.classifications[cs].css + '"';
            
            if (idea.pretty_pm === undefined) {
              var pretty_pm = '';
            } else {
              var pretty_pm = idea.pretty_pm.toUpperCase();
            }
            
            switch (attrs.type) {
            case 'compact':
              // compact - show abbreviated badge
              element.html($compile('<span class="classification compact clickable ' + className + '" ' + css + ' popover="' + pretty_pm + '" popover-trigger="mouseenter" popover-placement="left">' + cs.replace(/\W*(\w)\w*/g, '$1').toUpperCase() + '</span>')(scope));
              break;
            case 'text':
               // text - show only coloured text
                element.html('<span class="classification-text ' + className + '" style="color:' + pm.classifications[cs].colour + '" >' + pretty_pm + '</span>');
              break;
            default:
              // full - show with coloured banner and full text
                element.html($compile('<span class="classification clickable ' + className + '" ' + css + ' popover="' + pretty_pm + '" popover-trigger="mouseenter" popover-placement="top">' + classification + '</span>')(scope));
              break;
            }

          }
        }

      }, true);

      // $watch: wait until the scope has propagated before accessing, and watch for any changes (for when used on a form)
      scope.$watch('idea', function (idea) {
       
        if (idea !== undefined) {
          if (idea.classification_short !== undefined) {
            // if no classification selected or available then just quit...
            if (idea.classification_short === '') {
              return false;
            };

            var cs = idea.classification_short.toUpperCase();
            // !! look this up now from the PM api
            var classification = pm.classifications[cs].classification.toUpperCase();
            var className = pm.classifications[cs].class_name;
            var css = 'style="' + pm.classifications[cs].css + '"';
            
            if (idea.pretty_pm === undefined) {
              var pretty_pm = '';
            } else {
              var pretty_pm = idea.pretty_pm.toUpperCase();
            }
            
            switch (attrs.type) {
            case 'compact':
              // compact - show abbreviated badge
              element.html($compile('<span class="classification compact clickable ' + className + '" ' + css + ' popover="' + pretty_pm + '" popover-trigger="mouseenter" popover-placement="left">' + cs.replace(/\W*(\w)\w*/g, '$1').toUpperCase() + '</span>')(scope));
              break;
            case 'text':
               // text - show only coloured text
                element.html('<span class="classification-text ' + className + '" style="color:' + pm.classifications[cs].colour + '" >' + pretty_pm + '</span>');
              break;
            default:
              // full - show with coloured banner and full text
                element.html($compile('<span class="classification clickable ' + className + '" ' + css + ' popover="' + pretty_pm + '" popover-trigger="mouseenter" popover-placement="top">' + classification + '</span>')(scope));
              break;
            }

          }
        }

      }, true);      

      // $watch: wait until the scope has propagated before accessing, and watch for any changes (for when used on a form)
      scope.$watch('project', function (project) {
       
        if (project !== undefined) {
          if (project.classification_short !== undefined) {
            // if no classification selected or available then just quit...
            if (project.classification_short === '') {
              return false;
            };

            var cs = project.classification_short.toUpperCase();
            // !! look this up now from the PM api
            var classification = pm.classifications[cs].classification.toUpperCase();
            var className = pm.classifications[cs].class_name;
            var css = 'style="' + pm.classifications[cs].css + '"';
            
            if (project.pretty_pm === undefined) {
              var pretty_pm = '';
            } else {
              var pretty_pm = project.pretty_pm.toUpperCase();
            }
            
            switch (attrs.type) {
            case 'compact':
              // compact - show abbreviated badge
              element.html($compile('<span class="classification compact clickable ' + className + '" ' + css + ' popover="' + pretty_pm + '" popover-trigger="mouseenter" popover-placement="left">' + cs.replace(/\W*(\w)\w*/g, '$1').toUpperCase() + '</span>')(scope));
              break;
            case 'text':
               // text - show only coloured text
                element.html('<span class="classification-text ' + className + '" style="color:' + pm.classifications[cs].colour + '" >' + pretty_pm + '</span>');
              break;
            default:
              // full - show with coloured banner and full text
                element.html($compile('<span class="classification clickable ' + className + '" ' + css + ' popover="' + pretty_pm + '" popover-trigger="mouseenter" popover-placement="top">' + classification + '</span>')(scope));
              break;
            }

          }
        }

      }, true);      
      
      // $watch: wait until the scope has propagated before accessing, and watch for any changes (for when used on a form)
      scope.$watch('content', function (content) {
       
        if (content !== undefined) {
          if (content.classification_short !== undefined) {
            // if no classification selected or available then just quit...
            if (content.classification_short === '') {
              return false;
            };

            var cs = content.classification_short.toUpperCase();
            // !! look this up now from the PM api
            var classification = pm.classifications[cs].classification.toUpperCase();
            var className = pm.classifications[cs].class_name;
            var css = 'style="' + pm.classifications[cs].css + '"';
            
            if (content.pretty_pm === undefined) {
              var pretty_pm = '';
            } else {
              var pretty_pm = content.pretty_pm.toUpperCase();
            }
            
            switch (attrs.type) {
            case 'compact':
              // compact - show abbreviated badge
              element.html($compile('<span class="classification compact clickable ' + className + '" ' + css + ' popover="' + pretty_pm + '" popover-trigger="mouseenter" popover-placement="left">' + cs.replace(/\W*(\w)\w*/g, '$1').toUpperCase() + '</span>')(scope));
              break;
            case 'text':
               // text - show only coloured text
                element.html('<span class="classification-text ' + className + '" style="color:' + pm.classifications[cs].colour + '" >' + pretty_pm + '</span>');
              break;
            default:
              // full - show with coloured banner and full text
                element.html($compile('<span class="classification clickable ' + className + '" ' + css + ' popover="' + pretty_pm + '" popover-trigger="mouseenter" popover-placement="top">' + classification + '</span>')(scope));
              break;
            }

          }
        }

      }, true);
      
      // $watch: wait until the scope has propagated before accessing, and watch for any changes (for when used on a form)
      scope.$watch('feedback', function (feedback) {
       
        if (feedback !== undefined) {
          if (feedback.classification_short !== undefined) {
            // if no classification selected or available then just quit...
            if (feedback.classification_short === '') {
              return false;
            };

            var cs = feedback.classification_short.toUpperCase();
            // !! look this up now from the PM api
            var classification = pm.classifications[cs].classification.toUpperCase();
            var className = pm.classifications[cs].class_name;
            var css = 'style="' + pm.classifications[cs].css + '"';
            
            if (feedback.pretty_pm === undefined) {
              var pretty_pm = '';
            } else {
              var pretty_pm = feedback.pretty_pm.toUpperCase();
            }
            
            switch (attrs.type) {
            case 'compact':
              // compact - show abbreviated badge
              element.html($compile('<span class="classification compact clickable ' + className + '" ' + css + ' popover="' + pretty_pm + '" popover-trigger="mouseenter" popover-placement="left">' + cs.replace(/\W*(\w)\w*/g, '$1').toUpperCase() + '</span>')(scope));
              break;
            case 'text':
               // text - show only coloured text
                element.html('<span class="classification-text ' + className + '" style="color:' + pm.classifications[cs].colour + '" >' + pretty_pm + '</span>');
              break;
            default:
              // full - show with coloured banner and full text
                element.html($compile('<span class="classification clickable ' + className + '" ' + css + ' popover="' + pretty_pm + '" popover-trigger="mouseenter" popover-placement="top">' + classification + '</span>')(scope));
              break;
            }

          }
        }

      }, true);

    }
  };
});

/************************************************************************
 *  maxProtectiveMarking
 *    creates the maximum protective marking banner per page content
 *    include with:
 *      <max-protective-marking></max-protective-marking>
 *************************************************************************/
ideaworks.ngDirectives.directive('maxProtectiveMarking', function ($compile) {
  return {
    restrict : 'AEMC',
    replace : 'true',
    template : '<span></span>',
    link : function (scope, element, attrs) {
      var pm = scope.pm;
      var max_pm = scope.max_pm;
      // $watch: wait until the scope has propagated before accessing, and watch for any changes (for when used on a form)
      scope.$watch('max_pm', function (max_pm) {

        if (max_pm !== undefined) {
          var cs = max_pm.classification_short.toUpperCase() ? max_pm.classification_short.toUpperCase() : 'O';
          // !! look this up now from the PM api
          var className = pm.classifications[cs].class_name;
          var css = 'style="' + pm.classifications[cs].css + '"';
          var classification = pm.classifications[cs].classification;
          var descriptor = max_pm.descriptor ? ' [' + max_pm.descriptor + ']' : '';
          var codewords = ' ' + max_pm.codewords.join('/');
          var nc = ' ' + max_pm.national_caveats_primary_name;
          element.html($compile('<span class="classification clickable ' + className + '" ' + css + ' popover-title="   Maximum Protective Marking   " popover-placement="bottom" popover="' + classification + descriptor + codewords + nc + '" popover-trigger="mouseenter">' + classification + '</span>')(scope));        
              
        }

      }, true)
    }
  };
});


/************************************************************************
 *  commentProtectiveMarking
 *    creates the protective marking banner per comment
 *    include with:
 *      <comment-protective-marking></comment-protective-marking>
 *************************************************************************/
ideaworks.ngDirectives.directive('commentProtectiveMarking', function ($compile) {
  return {
    restrict : 'AEMC',
    replace : 'true',
    template : '<span></span>',
    link : function (scope, element, attrs) {
      var pm = scope.pm;
      
       // $watch: wait until the scope has propagated before accessing, and watch for any changes (for when used inside ng-repeat)
      scope.$watch('comment', function (comment) {
        if (comment !== undefined) {
        var cs = comment.protective_marking.classification_short.toUpperCase();
        // !! look this up now from the PM api
        var classification = pm.classifications[cs].classification.toUpperCase();
        // !! look this up now from the PM api
        var className = pm.classifications[cs].class_name;
        var css = 'style="' + pm.classifications[cs].css + '"';
        
        element.html($compile('<span class="classification compact clickable ' + className + '" ' + css + ' popover="' + comment.protective_marking.pretty_pm + '" popover-trigger="mouseenter" >' + classification.replace(/\W*(\w)\w*/g, '$1').toUpperCase() + '</span>')(scope));
        }
        });

    }
  };
});

/************************************************************************
 *  viewLoading
 *    used to show a loading message/image while view
 *    data loads inside an ng-repeat
 *************************************************************************/
ideaworks.ngDirectives.directive('viewLoading', function () {
  return function (scope, element, attrs) {
    if (scope.$last) {
      scope.$eval('doViewLoaded()');
    }
  }
});

/************************************************************************
 *  viewIdeaTags
 *    used to display idea tags in views/grids
 *      include with:
 *      <view-idea-tags type=""></view-idea-tags>
 *        where type [optional] is compact, or count-only
 *      default [no type]: displays list of tags in full
 *      compact: displays multiple tags on a single button with a count
 *                but if only a single tag it displays it in full
 *      count-only: displays just tag count even if only 1 tag
 *************************************************************************/
ideaworks.ngDirectives.directive('viewIdeaTags', function ($compile, $sce) {
  return {
    restrict : 'AEMC',
    replace : 'true',
    template : '<span></span>',
    link : function (scope, element, attrs) {
      var tag_count = scope.idea.tags.length;
      var tagTemplate = '';
      if (attrs.type === 'count-only') {
        if (tag_count > 1) {
          tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" popover="{{idea.tag_list}}"  popover-title="{{idea.tag_count}} tags" popover-trigger="mouseenter" ng-click="filterByTag(\'' + scope.idea.tag_list.split(', ').join() + '\')">';
          tagTemplate += '  <i class="icon-tags" ></i> &nbsp; {{idea.tag_count}}';
          tagTemplate += '</button>';
        } else {
          tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" popover="{{idea.tag_list}}"  popover-title="1 tag" popover-trigger="mouseenter" ng-click="filterByTag(\'' + scope.idea.tag_list + '\')">';
          tagTemplate += '  <i class="icon-tag" ></i> &nbsp; 1';
          tagTemplate += '</button>';
        }
      } else {
        if (attrs.type === 'compact') {
          if (tag_count > 1) {
            tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" popover="{{idea.tag_list}}"  popover-title="{{idea.tag_count}} tags" popover-trigger="mouseenter" ng-click="filterByTag(\'' + scope.idea.tag_list.split(', ').join() + '\')">';
            tagTemplate += '  <i class="icon-tags" ></i> &nbsp; {{idea.tag_count}}';
            tagTemplate += '</button>';
          } else {
            tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" popover="{{idea.tag_list}}"  popover-title="1 tag" popover-trigger="mouseenter" ng-click="filterByTag(\'' + scope.idea.tag_list + '\')">';
            tagTemplate += '  <i class="icon-tag" ></i> &nbsp; {{idea.tag_list}}';
            tagTemplate += '</button>';
          }
        } else {
          if (tag_count > 1) {
            angular.forEach(scope.idea.tag_list.split(','), function (tag, key) {
              tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" ng-class="{\'btn-info\':isTagSelected(\'' + tag.trim() + '\')}" ng-click="filterByTag(\'' + tag.trim() + '\')">';
              tagTemplate += '  <i class="icon-tag" ></i> &nbsp; ' + tag;
              tagTemplate += '</button>';
            });
          } else {
            tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" ng-click="filterByTag(\'' + scope.idea.tag_list + '\')">';
            tagTemplate += '  <i class="icon-tag" ></i> &nbsp; {{idea.tag_list}}';
            tagTemplate += '</button>';
          }
        }
      };

      // recompile or the ui pop-overs won't work
      element.html($compile(tagTemplate)(scope));
    }
  };
});


/************************************************************************
 *  viewProjectTags
 *    used to display project tags in views/grids
 *      include with:
 *      <view-project-tags type=""></view-project-tags>
 *        where type [optional] is compact, or count-only
 *      default [no type]: displays list of tags in full
 *      compact: displays multiple tags on a single button with a count
 *                but if only a single tag it displays it in full
 *      count-only: displays just tag count even if only 1 tag
 *************************************************************************/
ideaworks.ngDirectives.directive('viewProjectTags', function ($compile, $sce) {
  return {
    restrict : 'AEMC',
    replace : 'true',
    template : '<span></span>',
    link : function (scope, element, attrs) {
      var tag_count = scope.project.tags.length;
      var tagTemplate = '';
      if (attrs.type === 'count-only') {
        if (tag_count > 1) {
          tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" popover="{{project.tag_list}}"  popover-title="{{project.tag_count}} tags" popover-trigger="mouseenter" ng-click="filterByTag(\'' + scope.project.tag_list.split(', ').join() + '\')">';
          tagTemplate += '  <i class="icon-tags" ></i> &nbsp; {{project.tag_count}}';
          tagTemplate += '</button>';
        } else {
          tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" popover="{{project.tag_list}}"  popover-title="1 tag" popover-trigger="mouseenter" ng-click="filterByTag(\'' + scope.project.tag_list + '\')">';
          tagTemplate += '  <i class="icon-tag" ></i> &nbsp; 1';
          tagTemplate += '</button>';
        }
      } else {
        if (attrs.type === 'compact') {
          if (tag_count > 1) {
            tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" popover="{{project.tag_list}}"  popover-title="{{project.tag_count}} tags" popover-trigger="mouseenter" ng-click="filterByTag(\'' + scope.project.tag_list.split(', ').join() + '\')">';
            tagTemplate += '  <i class="icon-tags" ></i> &nbsp; {{project.tag_count}}';
            tagTemplate += '</button>';
          } else {
            tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" popover="{{project.tag_list}}"  popover-title="1 tag" popover-trigger="mouseenter" ng-click="filterByTag(\'' + scope.project.tag_list + '\')">';
            tagTemplate += '  <i class="icon-tag" ></i> &nbsp; {{project.tag_list}}';
            tagTemplate += '</button>';
          }
        } else {
          if (tag_count > 1) {
            angular.forEach(scope.project.tag_list.split(','), function (tag, key) {
              tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" ng-class="{\'btn-info\':isTagSelected(\'' + tag.trim() + '\')}" ng-click="filterByTag(\'' + tag.trim() + '\')">';
              tagTemplate += '  <i class="icon-tag" ></i> &nbsp; ' + tag;
              tagTemplate += '</button>';
            });
          } else {
            tagTemplate += '<button class="btn btn-mini btn-tag disabled clickable" ng-click="filterByTag(\'' + scope.project.tag_list + '\')">';
            tagTemplate += '  <i class="icon-tag" ></i> &nbsp; {{project.tag_list}}';
            tagTemplate += '</button>';
          }
        }
      };

      // recompile or the ui pop-overs won't work
      element.html($compile(tagTemplate)(scope));
    }
  };
});

/************************************************************************
 *  runJquery
 *      add the <run-jquery></run-jquery> directive to the foot of any
 *      templates that need to run jQuery AFTER angular has loaded
 *************************************************************************/
ideaworks.ngDirectives.directive('runJquery', function ($timeout) {
  return {
    restrict : 'AEMC',
    link : function () {

      $timeout(function () {
        // //#console.log('apply jQuery DOM stuff now...');
        /* ------ jQuery code here ------------------- */

        // $('.selectpicker').selectpicker();

        /*-------------------------------------------- */
      }, 10, false);
      //  });
    }
  };
});