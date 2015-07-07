"""
Email application main module.
"""
from gi.repository import GObject

import pisak
from pisak import app_manager, res, logger, exceptions
from pisak.libs import handlers
from pisak.libs.viewer import model
from pisak.libs.email import address_book, message, imap_client

from pisak.libs.email import widgets  # @UnusedImport
import pisak.libs.email.handlers  # @UnusedImport
import pisak.libs.speller.handlers  # @UnusedImport
import pisak.libs.speller.widgets  # @UnusedImport
import pisak.libs.viewer.widgets  # @UnusedImport

_LOG = logger.get_logger(__name__)

MESSAGES = {
    "no_internet": "Brak połączenia z internetem.\nSprawdź"
                   "łącze i spróbuj ponownie",
    "login_fail": "Błąd podczas logowania. Sprawdź swoje ustawienia\n"
                    "skrzynki i spróbuj ponownie.",
    "empty_mailbox": "Brak wiadomości w skrzynce.",
    "invalid_sent_box_name": "Nieprawidłowa nazwa skrzynki wysłanych.",
    "invalid_email_address": "Podałeś błędny adres email.\n"
                "Adres powinien zawierać znak @ i kropkę w nazwie domeny.\n"
                "Na przykład:     JanKowalski@gmail.com",
    "message_send_fail": "Wysyłanie wiadomości nie powiodło się.\n"
                         "Sprawdź połączenie z internetem i spróbuj ponownie.",
    "invalid_credentials": "Nieprawidłowa nazwa użytkownika lub hasło.",
    "unknown": "Wystąpił błąd. Spróbuj ponownie."
}


ELEMENTS = {
    "new_message": message.SimpleMessage(),
    "address_book": address_book.AddressBook(),
    "imap_client": imap_client.IMAPClient()
}


VIEWS_MAP = {
    "new_message_initial_view": "email/speller_message_subject"
}


BUILTIN_CONTACTS = [
    {
        "name": "PISAK",
        "address": "kontakt@pisak.org",
        "photo": res.get("logo_pisak.png")
    }
]


def prepare_main_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_inbox", "email/inbox")
    handlers.button_to_view(window, script, "button_sent", "email/sent")
    handlers.button_to_view(window, script, "button_drafts", "email/drafts")
    handlers.button_to_view(
        window, script, "button_address_book", "email/address_book")
    handlers.button_to_view(window, script, "button_new_message",
        VIEWS_MAP["new_message_initial_view"])

    for contact in BUILTIN_CONTACTS:
        try:
            app.box["address_book"].add_contact(contact)
        except address_book.AddressBookError as e:
            pass  # TODO: notify the user

    counter_label = '  ( {} )'

    try:
        contact_count = app.box["address_book"].get_count()
        window.ui.button_address_book.set_label(
            window.ui.button_address_book.get_label() +
            counter_label.format(str(contact_count))
        )
    except address_book.AddressBookError as e:
        pass  # TODO: say something

    client = app.box["imap_client"]
    try:
        try:
            client.login()
        except imap_client.InvalidCredentials as e:
            window.load_popup(MESSAGES["invalid_credentials"], app.main_quit)
        except imap_client.IMAPClientError as e:
            window.load_popup(MESSAGES["login_fail"], app.main_quit)
        else:
            try:
                inbox_all, inbox_unseen =  client.get_inbox_status()
                window.ui.button_inbox.set_label(
                    window.ui.button_inbox.get_label() +
                    counter_label.format("  /  ".join([str(inbox_unseen), str(inbox_all)]))
                )
            except imap_client.IMAPClientError as e:
                pass  # TODO: do something

            try:
                sent_box_count = client.get_sent_box_count()
                window.ui.button_sent.set_label(
                    window.ui.button_sent.get_label() +
                    counter_label.format(str(sent_box_count))
                )
            except imap_client.IMAPClientError as e:
                pass # TODO: display some warning
    except exceptions.NoInternetError as e:
        window.load_popup(MESSAGES["no_internet"], app.main_quit)


def prepare_drafts_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(
        window, script, "button_new_message",
        VIEWS_MAP["new_message_initial_view"])
    handlers.button_to_view(window, script, "button_back", "email/main")


def prepare_inbox_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(
        window, script, "button_new_message",
        VIEWS_MAP["new_message_initial_view"])
    handlers.button_to_view(window, script, "button_back", "email/main")
    data_source = script.get_object("data_source")
    data_source.item_handler = lambda tile, message_preview: \
        window.load_view(
            "email/single_message",
            {
                "message_uid": message_preview.content["UID"],
                "message_source":
                    app.box["imap_client"].get_message_from_inbox,
                "previous_view": "inbox"
            }
        )

    inbox_list = []
    try:
        inbox_list = app.box["imap_client"].get_inbox_list()[::-1]
    except imap_client.IMAPClientError as e:
        window.load_popup(MESSAGES["unknown"],
                          container=window.ui.pager)
    except exceptions.NoInternetError as e:
        window.load_popup(MESSAGES["no_internet"],
                          container=window.ui.pager)
    else:
        if len(inbox_list) == 0:
            window.load_popup(MESSAGES["empty_mailbox"],
                          container=window.ui.pager)
        else:
            data_source.data = data_source.produce_data(
                inbox_list, lambda msg: msg["Date"])


def prepare_sent_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(
        window, script, "button_new_message",
        VIEWS_MAP["new_message_initial_view"])
    handlers.button_to_view(window, script, "button_back", "email/main")

    data_source = script.get_object("data_source")
    data_source.item_handler = lambda tile, message_preview: \
        window.load_view(
            "email/single_message",
            {
                "message_uid": message_preview.content["UID"],
                "message_source":
                    app.box["imap_client"].get_message_from_sent_box,
                "previous_view": "sent"
            }
        )

    sent_box_list = []
    try:
        sent_box_list = app.box["imap_client"].get_sent_box_list()[::-1]
    except imap_client.IMAPClientError as e:
        window.load_popup(MESSAGES["invalid_sent_box_name"],
                          container=window.ui.pager)
    except exceptions.NoInternetError as e:
        window.load_popup(MESSAGES["no_internet"],
                          container=window.ui.pager)
    else:
        if len(sent_box_list) == 0:
            window.load_popup(MESSAGES["empty_mailbox"],
                          container=window.ui.pager)
        else:
            data_source.data = data_source.produce_data(
                sent_box_list, lambda msg: msg["Date"])


def prepare_speller_message_body_view(app, window, script, data):
    if data and 'original_msg' in data and data['original_msg'].get('Body'):
        body = '\n'.join(['> ' + line for line in
                          data['original_msg']['Body'].split('\n')])
        window.ui.text_box.type_text(body)

    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_proceed",
                    "email/address_book", {"pick_recipients_mode": True})


def prepare_speller_message_subject_view(app, window, script, data):
    if data and 'original_msg' in data:
        subject = data['original_msg']['Subject']
        action = data.get('action')
        if action == 'forward':
            pre = 'Fwd: '
        elif action in ('reply', 'reply_all'):
            pre = 'Re: '
        else:
            pre = ''

        window.ui.text_box.type_text(pre + subject)

    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_proceed",
                            "email/speller_message_body", data)


def prepare_speller_message_to_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_proceed", "email/sent")


def prepare_address_book_view(app, window, script, data):
    data_source = script.get_object("data_source")

    contacts = []
    try:
        contacts = app.box["address_book"].get_all_contacts()
    except address_book.AddressBookError as e:
        pass  # TODO: display warning and/or try to reload the view

    def on_contact_select(tile, contact):
        """
        On contact tile select.

        :param tile: tile representing single contact
        :param contact: contact dictionary
        """
        tile.toggled = contact.flags["picked"] = \
            not  contact.flags["picked"] if "picked" in contact.flags else True
        if tile.toggled:
            app.box["new_message"].recipients = contact.content.address
        else:
            app.box["new_message"].remove_recipient(contact.content.address)

    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_back", "email/main")

    if data and data.get("pick_recipients_mode"):
        specific_button= window.ui.button_send_message
        tile_handler = lambda tile, contact: on_contact_select(tile, contact)
        handlers.button_to_view(window, script,
                                "button_send_message", "email/sent")
    else:
        specific_button = window.ui.button_new_contact
        tile_handler = lambda tile, contact: window.load_view(
            "email/contact", {"contact_id": contact.content.id})
        handlers.button_to_view(
            window, script, "button_new_contact", "email/speller_contact_address")

    window.ui.button_menu_box.replace_child(
        window.ui.button_specific, specific_button)
    data_source.item_handler = tile_handler

    data_source.data = sorted(data_source.produce_data(
        contacts, lambda contact:
        contact.name if contact.name else contact.address))


def prepare_contact_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_back", "email/main")

    if data:
        try:
            contact = app.box["address_book"].get_contact(data["contact_id"])
        except address_book.AddressBookError as e:
            contact = None  # TODO: display warning
        if contact:
            window.ui.contact_address_text.set_text(contact.address)
            if contact.name:
                window.ui.contact_name_text.set_text(contact.name)
            if contact.photo:
                try:
                    window.ui.photo.set_from_file(contact.photo)
                except GObject.GError as e:
                    _LOG.error(e)

            def add_recipient():
                app.box["new_message"].recipients = contact.address

            handlers.connect_button(
                script, "button_create_message", add_recipient)
            handlers.button_to_view(
                window, script, "button_create_message",
                "email/speller_message_subject")
            handlers.button_to_view(
                window, script, "button_edit_name",
                "email/speller_contact_name",
                {"contact_id": contact.id, "contact_name": contact.name})
            handlers.button_to_view(
                window, script, "button_edit_address",
                "email/speller_contact_address",
                {"contact_id": contact.id, "contact_address": contact.address})
            handlers.button_to_view(
                window, script, "button_edit_photo",
                "email/viewer_contact_library",
                {"contact_id": contact.id, "contact_photo": contact.photo})


def prepare_speller_contact_name_view(app, window, script, data):
    def edit_contact_name():
        try:
            app.box["address_book"].edit_contact_name(
                data["contact_id"], window.ui.text_box.get_text())
        except  address_book.AddressBookError as e:
            pass  # TODO: display warning

    handlers.button_to_view(window, script, "button_exit")
    handlers.connect_button(script, "button_proceed", edit_contact_name)
    handlers.button_to_view(window, script, "button_proceed", "email/contact",
                            {"contact_id": data["contact_id"]})

    if data.get("contact_name"):
        window.ui.text_box.type_text(data["contact_name"])


def prepare_speller_contact_address_view(app, window, script, data):
    text_box = window.ui.text_box

    if not data or (data and data.get("new")):
        def create_contact():
            address = text_box.get_text()
            if address:
                try:
                    res = app.box["address_book"].add_contact(
                        {"address": address})
                    if not res:
                        # TODO: say that address is not unique
                        pass
                    contact = app.box["address_book"].get_contact_by_address(
                        address)
                    load = ("email/speller_contact_name", {"contact_id": contact.id})
                except address_book.AddressBookError as e:
                    # TODO: notify about failure
                    load = ("email/address_book")
            else:
                load = "email/address_book"

            window.load_view(*load)

        button_proceed_handler = create_contact
    else:
        if data.get("contact_address"):
            text_box.type_text(data["contact_address"])

        def edit_contact_address():
            try:
                app.box["address_book"].edit_contact_address(
                    data["contact_id"], text_box.get_text())
            except address_book.AddressBookError as e:
                pass  # TODO: display warning

            window.load_view("email/contact", {"contact_id": data["contact_id"]})

        button_proceed_handler = edit_contact_address

    handlers.button_to_view(window, script, "button_exit")
    handlers.connect_button(script, "button_proceed", button_proceed_handler)


def prepare_viewer_contact_library_view(app, window, script, data):
    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script, "button_back", "email/contact",
                            {"contact_id": data["contact_id"]})

    tile_source = script.get_object("library_data")
    tile_source.item_handler = lambda tile, album: window.load_view(
        "email/viewer_contact_album",
        {"album_id": album, "contact_id": data["contact_id"]})


def prepare_viewer_contact_album_view(app, window, script, data):
    contact_id = data["contact_id"]

    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(
        window, script, "button_library", "email/viewer_contact_library",
        {"contact_id": contact_id})

    album_id = data["album_id"]
    library = model.get_library()
    header = script.get_object("header")
    header.set_text(library.get_category_by_id(album_id).name)
    data_source = script.get_object("album_data")

    def photo_tile_handler(tile, photo_id, album_id):
        try:
            app.box["address_book"].edit_contact_photo(
                contact_id, library.get_item_by_id(photo_id).path)
        except address_book.AddressBookError as e:
            pass  # TODO: display warning
        window.load_view("email/contact", {"contact_id": contact_id})

    data_source.item_handler = photo_tile_handler
    data_source.data_set_id = album_id


def prepare_single_message_view(app, window, script, data):
    box = data["previous_view"]
    msg_id = data["message_uid"]

    def remove_message():
        if box == 'sent':
            app.box['imap_client'].delete_message_from_sent_box(msg_id)
        elif box == 'inbox':
            app.box['imap_client'].delete_message_from_inbox(msg_id)

        window.load_view('email/{}'.format(box))

    handlers.button_to_view(window, script, "button_exit")
    handlers.button_to_view(window, script,
                            "button_back", "email/{}".format(box))
    handlers.connect_button(script, "button_remove", remove_message)
    handlers.button_to_view(window, script, "button_new_mail",
                            VIEWS_MAP["new_message_initial_view"])

    try:
        message = data["message_source"](data["message_uid"])
    except imap_client.IMAPClientError as e:
        window.load_popup(MESSAGES["unknown"],
                          container=window.ui.message_content)
    except exceptions.NoInternetError as e:
        window.load_popup(MESSAGES["no_internet"],
                          container=window.ui.message_content)
    else:
        window.ui.message_subject.set_text(message["Subject"])
        window.ui.from_content.set_text(
            "; ".join([record[0] + " <" + record[1] + ">" for
                       record in message["From"]]))
        window.ui.to_content.set_text(
            "; ".join([record[0] + " <" + record[1] + ">" for
                       record in message["To"]]))
        window.ui.date_content.set_text(str(message["Date"]))
        if "Body" in message:
            window.ui.message_body.set_text(message["Body"])

        def reply():
            app.box['new_message'].recipients = message['From'][0][1]
            window.load_view(VIEWS_MAP["new_message_initial_view"],
                             {'original_msg': message, 'action': 'reply'})

        def reply_all():
            app.box['new_message'].recipients = [msg[1] for msg in message['From']]
            window.load_view(VIEWS_MAP["new_message_initial_view"],
                             {'original_msg': message, 'action': 'reply_all'})

        def forward():
            window.load_view(VIEWS_MAP["new_message_initial_view"],
                             {'original_msg': message, 'action': 'forward'})

        handlers.connect_button(script, "button_replay", reply)
        handlers.connect_button(script, "button_replay_all", reply_all)
        handlers.connect_button(script, "button_forward", forward)


if __name__ == "__main__":
    pisak.init()
    email_app = {
        "app": "email",
        "type": "clutter",
        "elements": ELEMENTS,
        "views": [
            ("main", prepare_main_view),
            ("drafts", prepare_drafts_view),
            ("inbox", prepare_inbox_view),
            ("sent", prepare_sent_view),
            ("single_message", prepare_single_message_view),
            ("address_book", prepare_address_book_view),
            ("contact", prepare_contact_view),
            ("speller_message_body", prepare_speller_message_body_view),
            ("speller_message_to", prepare_speller_message_to_view),
            ("speller_message_subject", prepare_speller_message_subject_view),
            ("speller_contact_name", prepare_speller_contact_name_view),
            ("speller_contact_address", prepare_speller_contact_address_view),
            ("viewer_contact_library", prepare_viewer_contact_library_view),
            ("viewer_contact_album", prepare_viewer_contact_album_view)
        ]
    }
    app_manager.run(email_app)
