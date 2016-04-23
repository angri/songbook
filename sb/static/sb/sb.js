var sb = {};

sb.commentForm = function(container) {
  function reset() {
    container.find('.submit-formgroup').collapse('hide');
    container.find('textarea').val('').one('input', function() {
      container.find('.submit-formgroup').collapse('show');
    });
  }
  reset();
  container.find('form').on('submit', function(event) {
    event.preventDefault();
    var data = $(this).serialize();
    var url = this.action;
    $.post(url, data, function(result) {
      reset();
    });
  });
};

sb.updatePagePart = function(target) {
  return $.get(window.location.href, function(html) {
    html = $(html);
    if (target)
      target.replaceWith(html.find('#' + target.attr('id')));
    var lastCommentId = Number($('div.comment').eq(0).data('comment-id'));
    var newComments = $('<div></div>');
    html.find('div.comment').each(function(idx, elem) {
      var commentId = Number($(this).data('comment-id'));
      if (commentId <= lastCommentId)
        return false;
      newComments.append(elem);
    });
    newComments = newComments.find('.comment');
    $('div.comments').prepend(newComments.addClass('collapse'));
    setTimeout(function() { newComments.collapse('show'); }, 0);
  });
}

sb.initPartsInfo = function() {
  $('#partsinfo button.join-part, #partsinfo button.save-changes').click(function() {
    var joinFormContainer = $(this).parents('li').find('.join-form');
    var joinForm = joinFormContainer.find('> form');
    var partContainer = joinFormContainer.parents('ul#partsinfo > li');
    var data = joinForm.serialize();
    var action = joinForm.data('join-action');
    $.post(action, data, function(result) {
      joinFormContainer
        .collapse('hide')
        .one('hidden.bs.collapse', function() {
          partContainer.addClass('joined');
        });
      sb.updatePagePart(partContainer.find('.performers'));
    });
  });
  $('#partsinfo button.leave-part').click(function() {
    var joinFormContainer = $(this).parents('li').find('.join-form');
    var joinForm = joinFormContainer.find('> form');
    var partContainer = joinFormContainer.parents('ul#partsinfo > li');
    var data = joinForm.serialize();
    var action = joinForm.data('leave-action');
    $.post(action, data, function(result) {
      joinFormContainer
        .collapse('hide')
        .one('hidden.bs.collapse', function() {
          partContainer.removeClass('joined')
        });
      sb.updatePagePart(partContainer.find('.performers'));
    });
  });
  $('#partsinfo .remove-part-form form').on("submit", function(event) {
    event.preventDefault();
    var form = $(this);
    $.post(form.attr('action'), form.serialize(), function(result) {
      form.parents('ul#partsinfo > li').slideUp(function() {
        $(this).remove();
        sb.updatePagePart(null);
      });
    });
  });
};

sb.initLinks = function() {
  $('#add-a-link form').on('submit', function(event) {
    event.preventDefault();
    $.post($(this).attr('action'), $(this).serialize(), function(result) {
      sb.updatePagePart($('#links')).done(function() {
        sb.initLinks();
        $('#add-a-link').collapse('hide');
      });
    });
  });

  $('#links .remove-form form').on('submit', function(event) {
    event.preventDefault();
    var form = $(this);
    $.post(form.attr('action'), form.serialize(), function(result) {
      form.parents('ul#links > li').slideUp(function() {
        sb.updatePagePart($('#links'));
        $(this).remove();
      });
    });
  });

  $('#links .edit-form form').on('submit', function(event) {
    event.preventDefault();
    var form = $(this);
    $.post(form.attr('action'), form.serialize(), function(result) {
      sb.updatePagePart($('#links')).done(function() {
        sb.initLinks();
        form.parents('ul#links .edit-form').collapse('hide');
      });
    });
  });
};

sb.songInlineEdit = function() {
  sb.initPartsInfo();
  sb.initLinks();

  var addAPartForm = $('#add-a-part form');

  addAPartForm.on("submit", function(event) {
    event.preventDefault();
    var data = addAPartForm.serialize();
    var action = addAPartForm.attr('action');
    $.post(action, data, function(result) {
      sb.updatePagePart($('#partsinfo')).done(function() {
        sb.initPartsInfo();
        addAPartForm.parent().collapse('hide');
      });
    });
  });
};
