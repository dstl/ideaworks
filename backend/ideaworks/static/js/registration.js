/*  Login and Registration form functions
    Use for pop up of Prototypes & Description of Service text in a neat dialog box
    Includes a dumb down fall back for < IE6
*/

$(function () {
  
  var thisForm = $('form').attr('id');
   //alert('This form id is : ' + thisForm);
  
  if (browser.isIE6()) { // use collapsible area for IE6
    $(".collapsible").on('click', function (){
      $($(this).attr('href')).toggleClass('expanded');
    });
  } else { // use jquery-ui pop-up dialog for other browsers
    //alert('Not using IE6');
    $( ".dialog-message" ).dialog({
      modal: true,
      autoOpen: false,
      width: 400,
      height: 400,
      buttons: {
        Ok: function() {
          $(this).dialog("close");
        }
      }
    });

    $( ".dialog-opener" ).click(function(e) {
      e.preventDefault();
      $( ".dialog-message" ).dialog( "open" );
    });
  }

  if (thisForm === 'login') {
    $('#id_username').focus();
  }
  
  if (thisForm === 'registration') {
    $('#id_email').focus();
  }
  
});

// some checks for IE6 etc..
var browser = {
  isIE6: function() {if($('html').hasClass('lt-ie7')) {return true} else {return false}}
}