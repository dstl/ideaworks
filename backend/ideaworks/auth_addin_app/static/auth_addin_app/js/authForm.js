/************************************************************************
 * authForm.js *
 *
 * JS Code for authorisation related forms. Includes some dumb down fall backs for < IE6
 * Author:  Russell King
 * Date:    Feb 2014
 *
 * Dependencies:  jQuery 1.10x, jQuery UI 1.10x
 *
 **************************************************************************/

/************************************************************************
 *  authForm
 *    main name-space
 *************************************************************************/
var authForm = {

  // globals
  formId : $('form').attr('id'),
  hasErrors : false,
  errorFields : null,

  /************************************************************************
   *  authForm.init()
   *************************************************************************/
  init : function () {

    // run specific form.init based on form id
    authForm[authForm.formId].init();

    // bind validation function to submit button
    $('#' + authForm.formId).on('submit', function (e) {
      authForm.validate(e);
    });

    // Pop up for most browsers, collapsible area for IE6.....
    if (browser.isIE6()) { // use collapsible area for IE6
      // alert('Using IE6 !!!! Boooo!');
      $(".collapsible").on('click', function () {
        $($(this).attr('href')).toggleClass('expanded');
      });
    } else { // use jquery-ui pop-up dialog for other browsers
      //alert('Not using IE6');
      $(".dialog-message").dialog({
        modal : true,
        autoOpen : false,
        width : 400,
        height : 400,
        buttons : {
          Ok : function () {
            $(this).dialog("close");
          }
        }
      });

      $(".dialog-opener").click(function (e) {
        console.log(this, $(this).attr('id').split('a_')[1]);
        e.preventDefault();
        // $(".dialog-message").dialog("open");
        $("#" + $(this).attr('id').split('a_')[1]).dialog("open");
      });
    }

  }, // END authForm.init

  /************************************************************************
   *  authForm.validate()
   *************************************************************************/
  validate : function (e) {
    // console.log('Do validation.....');
    authForm.clearErrors();

    // run the form specific validation function...
    authForm[authForm.formId].validate();

    // check for errors and display...
    if (authForm.hasErrors) {
      // console.log('there are errors : ', authForm.errorFields);
      // focus cursor on first error found
      $('#id_' + authForm.errorFields[0]).focus();
      $('p.errorlist').show();
      // prevent form submission
      e.preventDefault();
    } else {
      return;
    }

  },

  /************************************************************************
   *  authForm.addError()
   *************************************************************************/
  addError : function (fieldName, errorMsg) {
    // flag as error
    authForm.hasErrors = true;

    // store field name
    authForm.errorFields.push(fieldName);

    // if a checkbox add error in a div above, otherwise add an li before label tag
    if ($('#id_' + fieldName).attr('type') == 'checkbox') {
      $('#id_' + fieldName).parent().before('<div class="errorlist">' + errorMsg + '</div>');
    } else {
      $('#id_' + fieldName).prev().before('<ul class="errorlist"><li>' + errorMsg + '</li></ul>');
    //  $('#id_' + fieldName).after('<ul class="errorlist"><li>' + errorMsg + '</li></ul>');
      $('#id_' + fieldName).prev().addClass('has-error');
      $('#id_' + fieldName).addClass('has-error');
    }
  },

  /************************************************************************
   *  authForm.clearErrors()
   *************************************************************************/
  clearErrors : function () {
    // clear existing errors
    $('ul.errorlist, div.errorlist').remove();
    $('p.errorlist').hide();
    $('.has-error').removeClass('has-error');
    authForm.hasErrors = false,
    authForm.errorFields = [];
  },

  /*  Form specific functions....  */

  /************************************************************************
   *  authForm.registration
   *   functions specific to the registration form
   *************************************************************************/
  registration : {

    // init registration form
    init : function () {
      $('#id_email').focus();
    },

    // validate registration form
    validate : function () {

      if ($('#id_email').val() === '') {
        authForm.addError('email', '*This value is required.');
      } else {
        var emailRegExp = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        if (!emailRegExp.test($('#id_email').val())) {
          authForm.addError('email', '*Invalid email address.');
        }
      }

      if ($('#id_password1').val() === '') {
        authForm.addError('password1', '*This value is required.');
      }

      if ($('#id_password2').val() === '') {
        authForm.addError('password2', '*This value is required.');
      } else {
        if ($('#id_password1').val() !== $('#id_password2').val()) {
          authForm.addError('password2', '*Passwords do not match.');
        }
      }

      if ($('#id_first_name').val() === '') {
        authForm.addError('first_name', '*This value is required.');
      }

      if ($('#id_last_name').val() === '') {
        authForm.addError('last_name', '*This value is required.');
      }

      if ($('#id_organisation').val() === '') {
        authForm.addError('organisation', '*This value is required.');
      }

      if ($('#id_team').val() === '') {
        authForm.addError('team', '*This value is required.');
      }

      if ($('#id_tos').prop('checked') === false) {
        authForm.addError('tos', '*You must agree to the terms of service.');
      }
    }
  },

  /************************************************************************
   *  authForm.login
   *     functions specific to the login form
   *************************************************************************/
  login : {
    // init login form
    init : function () {
      $('#id_username').focus();
    },
    
    // validate login form
    validate : function () {
    
      if ($('#id_username').val() === '') {
        authForm.addError('username', '*This value is required.');
      }
      
      if ($('#id_password').val() === '') {
        authForm.addError('password', '*This value is required.');
      }
    }
  },

  /************************************************************************
   *  authForm.passwordChange
   *     functions specific to the password change form
   *************************************************************************/
  passwordChange : {
    // init form
    init : function () {
      $('#id_old_password').focus();
    },
    
    // validate form
    validate : function () {
      if ($('#id_old_password').val() === '') {
        authForm.addError('old_password', '*This value is required.');
      }
      
      if ($('#id_new_password1').val() === '') {
        authForm.addError('new_password1', '*This value is required.');
      }

      if ($('#id_new_password2').val() === '') {
        authForm.addError('new_password2', '*This value is required.');
      } else {
        if ($('#id_new_password1').val() !== $('#id_new_password2').val()) {
          authForm.addError('new_password2', '*Passwords do not match.');
        }
      }
    
    }
  }, 


  /************************************************************************
   *  authForm.passwordReset
   *     functions specific to the password change form
   *************************************************************************/
  passwordReset : {
    // init form
    init : function () {
      $('#id_email').focus();
    },
    
    // validate form
    validate : function () {
      if ($('#id_email').val() === '') {
        authForm.addError('email', '*This value is required.');
      }
    }
  }
}
/******************** END authForm ********************/
//
//

/************************************************************************
 *  Run code when DOM loaded...
 *************************************************************************/
$(document).ready(
  function () {
  // initialise auth Form
  authForm.init();
});

// some checks for IE6 etc..
var browser = {
  isIE6 : function () {
    if ($('html').hasClass('lt-ie7')) {
      return true
    } else {
      return false
    }
  }
};
