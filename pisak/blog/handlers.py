"""
Library of blog application specific signal handlers.
"""
import socket

import pisak
from pisak import signals, exceptions
from pisak.blog import wordpress


MESSAGES = {
    "publish-failed": "Nie udało się opublikować postu.\n"
                      "Sprawdź swoje łącze internetowe\n"
                      "i spróbuj jeszcze raz.",
    'timeout-expired-publish': 'Coś poszło nie tak.\nWejdź na swój blog '
                       'i sprawdź czy post został opublikowany.',
    'timeout-expired-delete': 'Coś poszło nie tak.\nWejdź na swój blog '
                       'i sprawdź czy post został usunięty.',
    'timeout-expired-bio': 'Coś poszło nie tak.\nWejdź na swój blog '
                       'i sprawdź czy profil został zaktualizowany.',
    'timeout-expired-photo': 'Coś poszło nie tak.\nWejdź na swój blog '
                       'i sprawdź czy zdjęcie zostało zmienione.',
}


@signals.registered_handler("blog/attach_post_content")
def attach_post_content(text_field):
    """
    Attach content to the currenlty edited post.

    :param text_field: text field that contains a content for the currently
    edited post.
    """
    post = wordpress.blog.pending_post
    if post is not None:
        wordpress.blog.attach_text(post, text_field.get_text())


@signals.registered_handler("blog/attach_post_title")
def attach_post_title(text_field):
    """
    Attach title to the currenlty edited post.

    :param text_field: text field that contains a title for the currently
    edited post.
    """
    post = wordpress.blog.pending_post
    if post is not None:
        post.title = text_field.get_text()


@signals.registered_handler("blog/publish_pending_post")
def publish_pending_post(source):
    """
    Publish the currently edited post.
    """
    try:
        wordpress.blog.attach_images(wordpress.blog.pending_post)
        wordpress.blog.publish_post(wordpress.blog.pending_post)
        wordpress.blog.pending_post = None
    except exceptions.PisakException:
        pisak.app.window.load_popup(MESSAGES['publish-failed'], 'blog/main')
    except socket.timeout:
        pisak.app.window.load_popup(MESSAGES['timeout-expired-publish'], 'main_panel/main')


@signals.registered_handler("blog/delete_pending_post")
def delete_pending_post(source):
    """
    Permanently delete the currently edited post from the blog.
    """
    if wordpress.blog.pending_post:
        try:
            wordpress.blog.delete_post(wordpress.blog.pending_post)
            wordpress.blog.pending_post = None
        except socket.timeout:
            pisak.app.window.load_popup(MESSAGES['timeout-expired-delete'], 'main_panel/main')


@signals.registered_handler("blog/publish_about_me_bio")
def publish_about_me_bio(text_field):
    """
    Publish about me informations.

    :param text_field: text field that contains about me informations.
    """
    try:
        wordpress.blog.update_about_me_bio(text_field.get_text())
    except socket.timeout:
        pisak.app.window.load_popup(MESSAGES['timeout-expired-bio'], 'main_panel/main')


def publish_about_me_photo(photo_path):
    """
    Publish my photo on the about me page.

    :param photo_path: photo path.
    """
    try:
        wordpress.blog.update_about_me_photo(photo_path)
    except socket.timeout:
        pisak.app.window.load_popup(MESSAGES['timeout-expired-photo'], 'main_panel/main')


@signals.registered_handler("blog/next_post")
def next_post():
    """
    Move to the view of the next post.
    """
    pass


@signals.registered_handler("blog/previous_post")
def previous_post():
    """
    Move to the view of the previous post.
    """
    pass


@signals.registered_handler("blog/scroll_post_up")
def scroll_post_up(post):
    """
    Scroll post upward. 
    
    :param post: post to be scrolled.
    """
    post.v_adj.set_value(post.v_adj.get_value() - post.v_adj.get_page_size()/2)

@signals.registered_handler("blog/scroll_post_down")
def scroll_post_down(post):
    """
    Scroll post downward. 
    
    :param post: post to be scrolled.
    """
    post.v_adj.set_value(post.v_adj.get_value() + post.v_adj.get_page_size()/2)


@signals.registered_handler("blog/go_back")
def go_back(post):
    """
    Display previous post from the posts list.
    
    :param post: post object.
    """
    post.view.go_back()

@signals.registered_handler("blog/go_forward")
def go_forward(post):
    """
    Display next post from the posts list.
    
    :param post: post object.
    """
    post.view.go_forward()
