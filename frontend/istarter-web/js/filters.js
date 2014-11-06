/* (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK */

'use strict';

/************************************************************************
 *  Filters
 *    ideaworks.ngFilters
 *************************************************************************/

ideaworks.ngFilters = angular.module('ideaworks.ngFilters', []);

/************************************************************************
 *  truncate
 *    usage;
 *     {{ textToTruncate | truncate:20 }}
 *************************************************************************/
ideaworks.ngFilters.filter('truncate', function () {
  return function (input, chars) {
    
    if (isNaN(chars)) return input;
    if (chars <=0) return '';
    if (input && input.length > chars) {
      // truncate the text
      return input.substring(0, chars) + ' . . .';
    } else {
      // don't truncate the text
      return input
    }
  }

});

/************************************************************************
 *  checkmark - use to create a tick or cross depending on input (true/false)
 *    usage;
 *     {{ text | checkmark }}
 *************************************************************************/
ideaworks.ngFilters.filter('checkmark', function() {
  return function(input) {
    if (input) {
      return input ? '\u2713' : '\u2718';
    } else {
      return input;
    }
  };
});

/************************************************************************
 *  hyphenate - use to create classnames etc...
 *    usage;
 *     {{ textToHyphenate | hyphenate }}
 *************************************************************************/
ideaworks.ngFilters.filter('hyphenate', function() {
  return function (input) {
    if (input) {
      return input.replace(/ +/g, '-');
    } else {
      return input;
    }
  };
});