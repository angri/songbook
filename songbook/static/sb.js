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
      sb.refreshAllComments();
    });
  });
};

// must be in sync with SB_COMMENTS_ON_PAGE setting
sb.COMMENTS_PAGE_SIZE = 20;

sb.REFRESH_COMMENTS_EVERY = 45000;

sb.comments = function(container) {
  container = $(container);
  var comments = {'container': container};
  var baseUrl = container.data('url');
  comments.limitNumComments = function(numCommentsToDisplay) {
    var toRemove = container.find('.comment').splice(numCommentsToDisplay, Infinity);
    var numToRemove = toRemove.length;
    if (numToRemove) {
      container.addClass('have-more');
      $(toRemove).remove();
    }
    return numToRemove;
  }
  comments.loadNewComments = function() {
    var newestCommentId = container.find('.comment:first-child').data('comment-id');
    var options = {};
    if (newestCommentId)
      options['not_before'] = newestCommentId;
    $.get(baseUrl, options, function(newComments) {
      newComments = $(newComments);
      var numCommentsToDisplay = container.find('.comment').length;
      if (numCommentsToDisplay < sb.COMMENTS_PAGE_SIZE)
        numCommentsToDisplay = sb.COMMENTS_PAGE_SIZE;
      if (newComments.length) {
        container.find('.comments-stream').prepend(newComments.hide());
        comments.limitNumComments(numCommentsToDisplay);
        setTimeout(function() {
          container.find('.comment:hidden').slideDown();
          container.trigger('newCommentsLoaded', [newComments]);
        }, 0);
      }
    });
  }
  comments.loadOldComments = function() {
    var oldestCommentId = container.find('.comment:last-child').data('comment-id');
    var options = {};
    if (oldestCommentId)
      options['not_after'] = oldestCommentId;
    $.get(baseUrl, options, function(oldComments) {
      var numCommentsToDisplay = container.find('.comment').length;
      numCommentsToDisplay += sb.COMMENTS_PAGE_SIZE;
      container.find('.comments-stream').append($(oldComments).hide());
      var removed = comments.limitNumComments(numCommentsToDisplay);
      if (removed == 0) {
        container.removeClass('have-more');
      }
      setTimeout(function() { container.find('.comment:hidden').slideDown(); }, 0);
    });
  }

  comments.limitNumComments(sb.COMMENTS_PAGE_SIZE);
  container.find('.load-more-line button').click(comments.loadOldComments);

  periodicallyLoadNewComments = function() {
    setTimeout(periodicallyLoadNewComments, sb.REFRESH_COMMENTS_EVERY);
    comments.loadNewComments();
  }
  setTimeout(periodicallyLoadNewComments, sb.REFRESH_COMMENTS_EVERY);

  container.get(0).setAttribute('data-comments', 1);
  container.data('comments', comments);
}

sb.commentsMarkAsViewed = function(container, form) {
  if (container.find('.comment-unread').length) {
    form.collapse('show');
  }
  container.on('newCommentsLoaded', function(event, newComments) {
    if (newComments.filter('.comment-unread').length) {
      form.collapse('show');
    }
  });
  form.on('submit', function(event) {
    event.preventDefault();
    $.post(form.attr('action'), form.serialize(), function(result) {
      form.collapse('hide');
      container.find('.comment-unread')
        .removeClass('comment-unread')
        .addClass('comment-seen');
      $('#unread-comments-notice').remove();
    });
  });
}

sb.refreshAllComments = function() {
  $('[data-comments]').data('comments').loadNewComments();
}

sb.updatePagePart = function(target) {
  return $.get(window.location.href, function(html) {
    html = $(html);
    target.replaceWith(html.find('#' + target.attr('id')));
  });
}

sb.initPartsInfo = function() {
  $('#partsinfo .join-form form, #partsinfo .part-edit-form form').on('submit', function(event) {
    event.preventDefault();
    var form = $(this);
    $.post(form.attr('action'), form.serialize(), function(result) {
      form.parent()
        .collapse('hide')
        .one('hidden.bs.collapse', function() {
          sb.updatePagePart($('#partsinfo')).done(sb.initPartsInfo);
        });
      sb.refreshAllComments();
    });
  });
  $('#partsinfo .leave-form form').on('submit', function(event) {
    event.preventDefault();
    var form = $(this);
    $.post(form.attr('action'), form.serialize(), function(result) {
      form.closest('.leave-form')
        .collapse('hide')
        .one('hidden.bs.collapse', function() {
          sb.updatePagePart($('#partsinfo')).done(sb.initPartsInfo);
        });
      sb.refreshAllComments();
    });
  });
  $('#partsinfo .remove-part-form form').on("submit", function(event) {
    event.preventDefault();
    var form = $(this);
    $.post(form.attr('action'), form.serialize(), function(result) {
      form.closest('.remove-part-form')
        .collapse('hide')
        .one('hidden.bs.collapse', function() {
          $(this).closest('li').remove();
        });
        sb.refreshAllComments();
    });
  });
};

sb.initLinks = function() {
  $('#links .remove-form form').on('submit', function(event) {
    event.preventDefault();
    var form = $(this);
    $.post(form.attr('action'), form.serialize(), function(result) {
      form.parents('ul#links > li').slideUp(function() {
        $(this).remove();
        sb.refreshAllComments();
      });
    });
  });

  $('#links .edit-form form').on('submit', function(event) {
    event.preventDefault();
    var form = $(this);
    $.post(form.attr('action'), form.serialize(), function(result) {
      var container = form.parents('ul#links > li');
      sb.updatePagePart(container.find('div.link-content')).done(function() {
        container.find('.edit-form').collapse('hide');
      });
      sb.refreshAllComments();
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
        addAPartForm.get(0).reset();
      });
      sb.refreshAllComments();
    });
  });

  $('#add-a-link form').on('submit', function(event) {
    event.preventDefault();
    $.post($(this).attr('action'), $(this).serialize(), function(result) {
      sb.updatePagePart($('#links')).done(function() {
        sb.initLinks();
        $('#add-a-link').collapse('hide').find('form').get(0).reset();
      });
      sb.refreshAllComments();
    });
  });
};

sb.watchUnwatch = function(form) {
  form.on('submit', function(event) {
    event.preventDefault();
    $.post(form.attr('action'), form.serialize(), function(result) {
      sb.updatePagePart(form);
    });
  });
}

sb.rangeSlider = function(container, choices) {
  var slider = container.find('input[type=range]');
  var displayValue = container.find('.display-value');
  slider.on('input', function() {
    var value = Number(slider.val());
    $.each(choices, function(idx, choice) {
      if (choice[0] == value) {
        displayValue.text(choice[1]);
        return false;
      }
    });
  }).trigger('input');
}

sb.highlightSetlist = function(initial) {
  var instrumentNames = {};
  $('.setlist .instrument').each(function(idx, elem) {
    instrumentNames[$(elem).data('instrument')] = elem.innerText;
  });

  if (initial) {
    var urlParts = location.href.split('#');
    if (urlParts.length == 2) {
      $('.setlist tbody').prepend($('.setlist tr.cutoff').detach());
      $.each(urlParts[1].split(',').reverse(), function(idx, songId) {
        var songLine = $('.setlist tr[data-song="' + songId + '"]').detach();
        $('.setlist tbody').prepend(songLine);
      });
    }
  }

  var performersBySong = [];
  var cutoffIndex = -1;
  $('.setlist tbody tr').each(function(idx, elem) {
    if ($(elem).is('.cutoff')) {
      cutoffIndex = idx;
      return;
    }
    var performers = {};
    $(elem).find('a.username').each(function(idx, elem) {
      var username = elem.innerText;
      if (!performers[username])
        performers[username] = new Set();
      var instrumentId = $(elem).closest('td').data('instrument');
      performers[username].add(instrumentNames[instrumentId]);
    });
    performersBySong.push(performers);
  });

  var songIds = [];
  $('.setlist tbody tr .changes').empty();
  $('.setlist tbody tr').each(function(idx, elem) {
    $(elem).find('.num').text(new String(idx + 1));

    songIds.push($(elem).data('song'));
    var changes = $(elem).find('.changes');
    changes.empty();
    if (idx == cutoffIndex - 1)
      return false;
    $.each(performersBySong[idx], function(performer, instruments) {
      var newInstruments = performersBySong[idx + 1][performer];
      if (newInstruments == instruments)
        return;
      if (! newInstruments) {
        changes.append($('<li class="out"></li>').text(performer));
        return;
      }

      var addedInstruments = [];
      var removedInstruments = [];
      newInstruments.forEach(function(instrument) {
        if (!instruments.has(instrument))
          addedInstruments.push(instrument);
      });
      instruments.forEach(function(instrument) {
        if (!newInstruments.has(instrument))
          removedInstruments.push(instrument);
      });

      var removedInstrStr = removedInstruments.join(", ");
      var addedInstrStr = addedInstruments.join(", ");
      if (addedInstruments.length && removedInstruments.length) {
        changes.append($(
          '<li class="change"><span class="who">' + performer + '</span> ' +
          '<span class="from">' + removedInstrStr + '</span> ' +
          '<span class="to">' + addedInstrStr + '</span></li>'
        ));
        return;
      }

      if (addedInstruments.length) {
        changes.append($(
          '<li class="change"><span class="who">' + performer + '</span> ' +
          '<span class="added">' + addedInstrStr + '</span></li>'
        ));
        return;
      }
    });
    $.each(performersBySong[idx + 1], function(performer, instruments) {
      if (! performersBySong[idx][performer]) {
        changes.append($('<li class="in"></li>').text(performer));
        return;
      }
    });

    changes.find('li.change').each(function(idx, change) {
      changes.append($(change).detach());
    });
  });

  window.history.replaceState({}, "", '#' + songIds.join(','));
};
