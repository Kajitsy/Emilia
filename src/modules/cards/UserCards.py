import base64

from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFileDialog, QFrame, QStackedWidget)

from modules.style.Elements import CustomTextEdit, PushButton, LineEdit, TabButton, VerticalScrollPage, CardFrame
from modules.QThreads import *
from modules.style.Icons import Svg
from modules.style.Utils import format_number, color_avatar
from modules.cards import VoiceCards, PersonaCards, CharacterCards, ScenesCards


class UserProfile(QWidget):
    def __init__(self, main_window, username):
        super().__init__(main_window)
        self.profile_id = None
        self.is_me = False
        self.data = {}
        self.me_following = []
        self.mw = main_window
        self.chat_thread = self.mw.chat_thread
        self.discord_thread  = self.mw.discord_thread
        self.svg_icons = self.mw.svg_icons

        self.initUI()

        self.profile_id = username
        self.is_me = self.profile_id == self.mw.username
        self.chat_thread.get_user_signal.connect(self._getUser)
        self.chat_thread.voices_search_username_signal.connect(self._getVoices)
        self.chat_thread.get_upvoted_characters_signal.connect(self._getUpCharacters)
        self.chat_thread.get_scenes_by_user_signal.connect(self._getScenes)
        self.chat_thread.get_user_personas_signal.connect(self._getUserPersonas)

        self.chat_thread.get_user(self.profile_id)
        self.chat_thread.voices_search_username(self.profile_id)
        self.chat_thread.get_scenes_by_user(self.profile_id)
        if self.is_me:
            self.chat_thread.get_user_personas()
            self.chat_thread.get_upvoted_characters()

    def initUI(self):
        self.top_bar, self.top_bar_layout = self.createTopBar()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        main_info_frame = QFrame(self)
        main_info_layout = QVBoxLayout()
        main_info_frame.setLayout(main_info_layout)
        layout.addWidget(main_info_frame)

        self.avatar_label = QLabel()
        self.avatar_label.setFixedSize(80, 80)
        main_info_layout.addWidget(self.avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-size: 18px;")
        main_info_layout.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.username_label = QLabel()
        self.username_label.setStyleSheet("color: #a2a2ac; font-size: 12px;")
        main_info_layout.addWidget(self.username_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        sub_frame = QFrame(self)
        sub_layout = QHBoxLayout()
        sub_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_frame.setLayout(sub_layout)
        layout.addWidget(sub_frame)

        self.followers_label = QLabel(self.tr("0 followers"))
        self.followers_label.mousePressEvent = lambda event: self.showFollowingFollowers("following")
        self.followers_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.followers_label.setStyleSheet("color: #a2a2ac;")
        sub_layout.addWidget(self.followers_label)

        span_label = QLabel("•")
        span_label.setStyleSheet("color: #a2a2ac;")
        sub_layout.addWidget(span_label)

        self.following_label = QLabel(self.tr("0 following"))
        self.following_label.mousePressEvent = lambda event: self.showFollowingFollowers("followers")
        self.following_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.following_label.setStyleSheet("color: #a2a2ac;")
        sub_layout.addWidget(self.following_label)

        span2_label = QLabel("|")
        span2_label.setStyleSheet("color: #a2a2ac;")
        sub_layout.addWidget(span2_label)

        self.chats_label = QLabel(self.tr("0 chats"))
        self.chats_label.setStyleSheet("color: #a2a2ac;")
        sub_layout.addWidget(self.chats_label)

        but_frame = QFrame(self)
        but_layout = QHBoxLayout()
        but_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        but_frame.setLayout(but_layout)
        layout.addWidget(but_frame)

        self.follow_button = PushButton(self.tr("Follow"))
        self.follow_button.setVisible(False)
        but_layout.addWidget(self.follow_button)

        self.edit_button = PushButton()
        self.edit_button.setIcon(self.svg_icons.settings())
        self.edit_button.clicked.connect(self.openUserSettings)
        but_layout.addWidget(self.edit_button)
        self.edit_button.setVisible(False)

        self.share_button = PushButton()
        self.share_button.setIcon(self.svg_icons.share())
        self.share_button.clicked.connect(self.share)
        but_layout.addWidget(self.share_button)

        content_layout = QVBoxLayout()

        buttons_frame = QFrame()
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        buttons_frame.setLayout(buttons_layout)
        content_layout.addWidget(buttons_frame)

        self.characters_button = TabButton(self.tr("Characters"))
        self.characters_button.setCheckable(True)
        self.characters_button.setChecked(True)
        self.characters_button.clicked.connect(lambda event: self.lists_widget.setCurrentWidget(self.character_list))
        self.characters_button.clicked.connect(lambda event: self.voices_button.setChecked(False))
        self.characters_button.clicked.connect(lambda event: self.up_characters_button.setChecked(False))
        self.characters_button.clicked.connect(lambda event: self.personas_button.setChecked(False))
        self.characters_button.clicked.connect(lambda event: self.scenes_button.setChecked(False))

        self.voices_button = TabButton(self.tr("Voices"))
        self.voices_button.setCheckable(True)
        self.voices_button.clicked.connect(lambda event: self.lists_widget.setCurrentWidget(self.voice_list))
        self.voices_button.clicked.connect(lambda event: self.characters_button.setChecked(False))
        self.voices_button.clicked.connect(lambda event: self.up_characters_button.setChecked(False))
        self.voices_button.clicked.connect(lambda event: self.personas_button.setChecked(False))
        self.voices_button.clicked.connect(lambda event: self.scenes_button.setChecked(False))

        self.scenes_button = TabButton(self.tr("Scenes"))
        self.scenes_button.setCheckable(True)
        self.scenes_button.clicked.connect(lambda event: self.lists_widget.setCurrentWidget(self.scenes_list))
        self.scenes_button.clicked.connect(lambda event: self.characters_button.setChecked(False))
        self.scenes_button.clicked.connect(lambda event: self.up_characters_button.setChecked(False))
        self.scenes_button.clicked.connect(lambda event: self.personas_button.setChecked(False))
        self.scenes_button.clicked.connect(lambda event: self.voices_button.setChecked(False))

        self.up_characters_button = TabButton(self.tr("Liked"))
        self.up_characters_button.setCheckable(True)
        self.up_characters_button.clicked.connect(lambda event: self.lists_widget.setCurrentWidget(self.upvoted_characters_list))
        self.up_characters_button.clicked.connect(lambda event: self.characters_button.setChecked(False))
        self.up_characters_button.clicked.connect(lambda event: self.voices_button.setChecked(False))
        self.up_characters_button.clicked.connect(lambda event: self.personas_button.setChecked(False))
        self.up_characters_button.clicked.connect(lambda event: self.scenes_button.setChecked(False))
        self.up_characters_button.setVisible(False)

        self.personas_button = TabButton(self.tr("Personas"))
        self.personas_button.setCheckable(True)
        self.personas_button.clicked.connect(lambda event: self.lists_widget.setCurrentWidget(self.personas_list))
        self.personas_button.clicked.connect(lambda event: self.characters_button.setChecked(False))
        self.personas_button.clicked.connect(lambda event: self.up_characters_button.setChecked(False))
        self.personas_button.clicked.connect(lambda event: self.voices_button.setChecked(False))
        self.personas_button.clicked.connect(lambda event: self.scenes_button.setChecked(False))
        self.personas_button.setVisible(False)

        buttons_layout.addWidget(self.characters_button)
        buttons_layout.addWidget(self.up_characters_button)
        buttons_layout.addWidget(self.personas_button)
        buttons_layout.addWidget(self.voices_button)
        buttons_layout.addWidget(self.scenes_button)

        self.character_list, self.character_list_layout = self.scroll_page()
        self.scenes_list, self.scenes_list_layout = self.scroll_page()
        self.upvoted_characters_list, self.upvoted_characters_layout = self.scroll_page()
        self.personas_list, self.personas_layout = self.scroll_page()
        self.voice_list, self.voice_list_layout = self.scroll_page()

        self.lists_widget = QStackedWidget()
        self.lists_widget.addWidget(self.character_list)
        self.lists_widget.addWidget(self.upvoted_characters_list)
        self.lists_widget.addWidget(self.personas_list)
        self.lists_widget.addWidget(self.voice_list)
        self.lists_widget.addWidget(self.scenes_list)
        self.lists_widget.setFixedWidth(600)
        self.lists_widget.setCurrentWidget(self.character_list)
        content_layout.addWidget(self.lists_widget, alignment=Qt.AlignmentFlag.AlignHCenter)

        layout.addLayout(content_layout)

        self.setLayout(layout)

    def openUserSettings(self):
        overlay = EditOverlay(self.mw)
        self.mw.showOverlay(overlay)

    def _getFollowing(self, data):
        self.chat_thread.me_following_signal.disconnect()
        self.me_following = data.get('following', [])

        if self.is_me:
            self.follow_button.setVisible(False)
            self.edit_button.setVisible(True)
            self.up_characters_button.setVisible(True)
            self.personas_button.setVisible(True)
        else:
            self.follow_button.setVisible(True)
            self.edit_button.setVisible(False)
            self.up_characters_button.setVisible(False)
            self.personas_button.setVisible(False)

        if self.username in self.me_following:
            self.follow_button.setText(self.tr("Unfollow"))
            self.follow_button.clicked.connect(self.unfollow)
        else:
            self.follow_button.clicked.connect(self.follow)

    def getFollowing(self):
        self.chat_thread.me_following_signal.connect(self._getFollowing)
        self.chat_thread.get_me_following()

    def _getVoices(self, data):
        self.chat_thread.voices_search_username_signal.disconnect()
        self.voice_data = data

        if self.voice_data:
            for voice in self.voice_data:
                card = VoiceCards.HorizontalMiniVoiceCard(self.mw, voice)
                self.voice_list_layout.addWidget(card)
        else:
            empty_label = QLabel(self.tr("And it's empty here..."))
            self.voice_list_layout.addWidget(empty_label, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _getUpCharacters(self, data):
        self.chat_thread.get_upvoted_characters_signal.disconnect()
        self.upvoted_characters = data

        if self.upvoted_characters:
            for character in self.upvoted_characters:
                card = CharacterCards.MainCard(self.mw, character['participant__name'], character.get('avatar_file_name'),
                                               character.get('title'), character.get('user__username'), character['external_id'],
                                               character["participant__num_interactions"], character["upvotes"], 70, 70)
                card.setFixedHeight(87)
                self.upvoted_characters_layout.addWidget(card)
        else:
            empty_label = QLabel(self.tr("And it's empty here..."))
            self.upvoted_characters_layout.addWidget(empty_label, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _getScenes(self, data):
        self.chat_thread.get_scenes_by_user_signal.disconnect()
        self.scenes = data

        if self.scenes:
            for scene in self.scenes:
                card = ScenesCards.ListCard(self.mw, scene)
                self.scenes_list_layout.addWidget(card)
        else:
            empty_label = QLabel(self.tr("And it's empty here..."))
            self.scenes_list_layout.addWidget(empty_label, alignment=Qt.AlignmentFlag.AlignHCenter)


    def _getUserPersonas(self, data):
        self.chat_thread.get_user_personas_signal.disconnect()
        self.user_personas = data

        if self.user_personas:
            for persona in self.user_personas:
                card = PersonaCards.MainCard(self.mw, persona)
                card.setFixedHeight(87)
                self.personas_layout.addWidget(card)

        button = PushButton(self.tr("New"))
        button.clicked.connect(lambda _: self.mw.showOverlay(PersonaCards.EditOverlay(self.mw)))
        self.personas_layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _getUser(self, data):
        self.chat_thread.get_user_signal.disconnect()
        self.getFollowing()
        self.data = data
        self.username = self.data.get('username')

        if self.data.get('avatar_file_name'):
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.data.get('avatar_file_name') + '?webp=true&anim=0',
                80, 80)
            load_avatar_thread.image_loaded.connect(self.avatar_label.setPixmap)
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            color_avatar(self.avatar_label, 80, 80, self.data.get('name'))

        if self.mw.drpc_enable and self.mw.drpc_show_current_page:
            if self.data.get('avatar_file_name') and self.mw.drpc_show_username:
                self.discord_thread.update(
                    details=self.tr("Looks at ") + self.username + self.tr("'s profile "),
                    large_image="https://characterai.io/i/80/static/avatars/" + self.data.get(
                        'avatar_file_name') + '?webp=true&anim=0',
                    buttons=[{
                        "label": "Open profile",
                        "url": f"https://character.ai/profile/{self.username}"
                    }]
                )
            elif self.mw.drpc_show_username:
                self.discord_thread.update(
                    details=self.tr("Looks at ") + self.username + self.tr("'s profile "),
                    buttons=[{
                        "label": "Open profile",
                        "url": f"https://character.ai/profile/{self.username}"
                    }]
                )
            else:
                self.discord_thread.update(details=self.tr("Looks at user profile"))

        chats_count = 0
        for character in self.data.get('characters', []):
            chats_count += character.get('participant__num_interactions', 0)
        chats_count = format_number(chats_count)

        self.name_label.setText(f"{self.data.get('name')}")
        self.username_label.setText(f"@{self.username}")
        self.followers_label.setText(format_number(self.data.get('num_followers')) + " " + self.tr("followers"))
        self.following_label.setText(format_number(self.data.get('num_following')) + " " + self.tr("following"))
        self.chats_label.setText(chats_count + " " + self.tr("chats"))
        if self.data.get('characters', []):
            for character in self.data.get('characters', []):
                card = CharacterCards.MainCard(self.mw, character['participant__name'], character.get('avatar_file_name'), character.get('title'), self.profile_id, character['external_id'], character["participant__num_interactions"], character["upvotes"], 70, 70)
                card.setFixedHeight(87)
                self.character_list_layout.addWidget(card)
        else:
            empty_label = QLabel(self.tr("And it's empty here..."))
            self.character_list_layout.addWidget(empty_label, alignment=Qt.AlignmentFlag.AlignHCenter)

    def share(self):
        QApplication.clipboard().setText(f'https://character.ai/profile/{self.username}')
        self.mw.showNotification(self.tr("Link copied to clipboard"))

    def scroll_page(self):
        f_page = QWidget()
        f_page_layout = QVBoxLayout(f_page)
        f_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        f_page.setLayout(f_page_layout)

        scroll_page = VerticalScrollPage()
        scroll_page.viewport.setStyleSheet("background-color: transparent; border: none;")
        scroll_layout = scroll_page.layout

        f_page_layout.addWidget(scroll_page)
        return f_page, scroll_layout

    def unfollow(self):
        def unfollow(self, data):
            self.follow_button.setText(self.tr("Follow"))
            self.follow_button.clicked.disconnect()
            self.follow_button.clicked.connect(self.follow)
        self.chat_thread.user_unfollow_signal.connect(lambda data: unfollow(self, data))
        self.chat_thread.user_unfollow(self.username)

    def follow(self):
        def follow(self, data):
            self.follow_button.setText(self.tr("Unfollow"))
            self.follow_button.clicked.disconnect()
            self.follow_button.clicked.connect(self.unfollow)
        self.chat_thread.user_follow_signal.connect(lambda data: follow(self, data))
        self.chat_thread.user_follow(self.username)

    def showFollowingFollowers(self, open_page="followers"):
        def openUser(username):
            self.mw.openUserPage(username)
            self.mw.hideOverlay()

        def follow(username, button: QPushButton):
            def follow(data):
                button.setText(self.tr("Unfollow"))
                button.clicked.disconnect()
                button.clicked.connect(lambda: unfollow(username, button))

            self.chat_thread.user_follow_signal.connect(lambda data: follow(data))
            self.chat_thread.user_follow(username)

        def unfollow(username, button: QPushButton):
            def unfollow(data):
                button.setText(self.tr("Follow"))
                button.clicked.disconnect()
                button.clicked.connect(lambda: follow(username, button))

            self.chat_thread.user_unfollow_signal.connect(lambda data: unfollow(data))
            self.chat_thread.user_unfollow(username)

        def _followers(data):
            self.chat_thread.user_followers_signal.disconnect()
            for user in data.get('users', {}):
                card = createCard(user)
                card.setFixedWidth(435)
                followers_users_layout.addWidget(card)

        def _following(data):
            self.chat_thread.user_following_signal.disconnect()
            for user in data.get('users', {}):
                card = createCard(user)
                card.setFixedWidth(435)
                following_users_layout.addWidget(card)

        def createCard(data):
            username = data.get("username")
            u_widget = CardFrame()
            u_widget.mousePressEvent = lambda event: openUser(username)
            u_widget.setCursor(Qt.CursorShape.PointingHandCursor)
            u_layout = QHBoxLayout(u_widget)
            u_widget.setLayout(u_layout)

            avatar_label = QLabel()
            avatar_label.setFixedSize(40, 40)
            if data.get('account__avatar_file_name'):
                load_avatar_thread = ImageLoaderThread(
                    "https://characterai.io/i/80/static/avatars/" + data.get('account__avatar_file_name') + '?webp=true&anim=0', 40, 40)
                load_avatar_thread.radius = 4
                load_avatar_thread.image_loaded.connect(avatar_label.setPixmap)
                load_avatar_thread.start()
                self.mw.threads.append(load_avatar_thread)
            else:
                color_avatar(avatar_label, 40, 40, username, 4)
            u_layout.addWidget(avatar_label)

            info_layout = QVBoxLayout()
            u_layout.addLayout(info_layout)
            name_label = QLabel(username)
            info_layout.addWidget(name_label, alignment=Qt.AlignmentFlag.AlignLeft)
            if data.get('account__bio'):
                bio = data.get('account__bio')
                if len(bio) > 45:
                    bio = data.get('account__bio')[:45] + "..."
                bio_label = QLabel(bio)
                bio_label.setStyleSheet("color: #a2a2ac;")
                info_layout.addWidget(bio_label, alignment=Qt.AlignmentFlag.AlignLeft)

            sub_button = PushButton()
            if not self.is_me:
                u_layout.addWidget(sub_button, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if username in self.me_following:
                    sub_button.setText(self.tr("Unfollow"))
                    sub_button.clicked.connect(lambda: unfollow(username, sub_button))
                else:
                    sub_button.setText(self.tr("Follow"))
                    sub_button.clicked.connect(lambda: follow(username, sub_button))
            return u_widget

        widget = QWidget()
        widget.setFixedSize(500, 750)
        layout = QVBoxLayout(widget)
        widget.setLayout(layout)

        buttons_frame = QFrame(widget)
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        buttons_frame.setLayout(buttons_layout)

        followers_button = TabButton(self.tr("Followers"))
        followers_button.setCheckable(True)
        followers_button.clicked.connect(lambda: pages_widget.setCurrentWidget(followers_page))
        followers_button.clicked.connect(lambda: following_button.setChecked(False))
        buttons_layout.addWidget(followers_button)

        following_button = TabButton(self.tr("Following"))
        following_button.setCheckable(True)
        following_button.clicked.connect(lambda: pages_widget.setCurrentWidget(following_page))
        following_button.clicked.connect(lambda: followers_button.setChecked(False))
        buttons_layout.addWidget(following_button)

        followers_page, followers_users_layout = self.scroll_page()
        following_page, following_users_layout = self.scroll_page()

        pages_widget = QStackedWidget()
        pages_widget.addWidget(followers_page)
        pages_widget.addWidget(following_page)
        if open_page == "followers":
            pages_widget.setCurrentWidget(following_page)
            following_button.setChecked(True)
        else:
            pages_widget.setCurrentWidget(followers_page)
            followers_button.setChecked(True)

        self.chat_thread.user_followers_signal.connect(_followers)
        self.chat_thread.user_following_signal.connect(_following)
        self.chat_thread.get_user_followers(username=self.username)
        self.chat_thread.get_user_following(username=self.username)

        layout.addWidget(buttons_frame)
        layout.addWidget(pages_widget, 1)
        self.mw.showOverlay(widget)

    def createTopBar(self):
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def showEvent(self, a0):
        super().showEvent(a0)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def hideEvent(self, a0):
        super().hideEvent(a0)
        self.mw.profile_button.setChecked(False)
        self.mw.profile_button_2.setChecked(False)
        self.deleteLater()

class EditOverlay(QFrame):
    def __init__(self, main_window):
        super().__init__()
        self.setFixedSize(500, 200)
        self.mw = main_window
        self.svg_icons = Svg()

        self.data = {
            "avatar_rel_path": self.mw.me.get('account',{}).get('avatar_file_name'),
            "avatar_type": self.mw.me.get('account', {}).get('avatar_type'),
            "bio": self.mw.me_full.get('bio'),
            "name": self.mw.me.get('account', {}).get('name'),
            "username": self.mw.me.get('username')
        }

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        fh_layout = QHBoxLayout()
        layout.addLayout(fh_layout)

        self.display_avatar = QLabel()
        self.display_avatar.mousePressEvent = lambda _: self.selectAvatar()
        self.display_avatar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.display_avatar.setFixedSize(70, 70)
        if self.data.get("avatar_file_name"):
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.data.get("avatar_file_name") + '?webp=true&anim=0',
                70, 70)
            load_avatar_thread.image_loaded.connect(self.display_avatar.setPixmap)
            load_avatar_thread.error_loading.connect(lambda _: color_avatar(self.mw.me_avatar, 70, 70, self.mw.name))
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        elif self.mw.me_has_avatar:
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + self.mw.me_avatar + '?webp=true&anim=0',
                70, 70)
            load_avatar_thread.image_loaded.connect(self.display_avatar.setPixmap)
            load_avatar_thread.error_loading.connect(lambda _: color_avatar(self.mw.me_avatar, 70, 70, self.mw.name))
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)
        else:
            color_avatar(self.display_avatar, 70, 70, self.mw.name)
        fh_layout.addWidget(self.display_avatar)

        names_layout = QVBoxLayout()
        fh_layout.addLayout(names_layout)

        self.display_name_edit = LineEdit()
        self.display_name_edit.setPlaceholderText(self.tr("Display Name"))
        self.display_name_edit.setText(self.data['name'])
        self.display_name_edit.setMaxLength(20)
        names_layout.addWidget(self.display_name_edit)

        self.username_edit = LineEdit()
        self.username_edit.setPlaceholderText(self.tr("Username"))
        self.username_edit.setText(self.data['username'])
        self.username_edit.setMaxLength(20)
        names_layout.addWidget(self.username_edit)

        self.bio_edit = CustomTextEdit()
        self.bio_edit.setPlaceholderText(self.tr("Background"))
        self.bio_edit.setText(self.data.get('bio'))
        self.bio_edit.textChanged.connect(lambda: self.textChanged(self.bio_edit, 500))
        self.bio_edit.setFixedHeight(32)
        self.bio_edit.horizontalScrollBar().setVisible(False)
        self.bio_edit.verticalScrollBar().setVisible(False)
        layout.addWidget(self.bio_edit)

        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.cancel_button = PushButton(self.tr("Cancel"))
        self.cancel_button.clicked.connect(self.mw.hideOverlay)
        button_layout.addWidget(self.cancel_button)

        self.save_button = PushButton(self.tr("Save"))
        self.save_button.clicked.connect(self.saveSettings)
        button_layout.addWidget(self.save_button)

    def textChanged(self, text_edit, max_len):
        text = text_edit.toPlainText()
        line_count = text.count('\n')
        line_count += text.count('<br>') + 1 if text else 1
        height = line_count * text_edit.fontMetrics().lineSpacing() + 32
        text_edit.setFixedHeight(height)
        if len(text) > max_len:
            text_edit.setPlainText(text[:max_len])
            cursor = text_edit.textCursor()
            cursor.setPosition(max_len)
            text_edit.setTextCursor(cursor)

    def selectAvatar(self):
        def uploaded(link):
            setattr(self, 'temp_link', link)
            self.data['avatar_rel_path'] = link
            self.data['avatar_type'] = "UPLOADED"
            load_avatar_thread = ImageLoaderThread(
                "https://characterai.io/i/80/static/avatars/" + link + '?webp=true&anim=0',
                60, 60)
            load_avatar_thread.image_loaded.connect(self.display_avatar.setPixmap)
            load_avatar_thread.start()
            self.mw.threads.append(load_avatar_thread)

        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.bmp)")
        if file_dialog.exec():
            file_path = file_dialog.selectedFiles()[0]
            if file_path.endswith(".png"):
                file_type = "png"
            elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                file_type = "jpeg"
            elif file_path.endswith(".bmp"):
                file_type = "bmp"

            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            self.mw.chat_thread.upload_avatar_signal.connect(uploaded)
            self.mw.chat_thread.upload_avatar(file_type, encoded)

    def saveSettings(self):
        self.data['bio'] = self.bio_edit.toPlainText()
        self.data['name'] = self.display_name_edit.text()
        self.data['username'] = self.username_edit.text()

        self.mw.me_full['user']['username'] = self.data['username']
        self.mw.me_full['user']['account']['name'] = self.data['name']
        self.mw.me_full['user']['account']['avatar_file_name'] = self.data['avatar_rel_path']
        self.mw.me_full['user']['account']['avatar_type'] = self.data['avatar_type']
        self.mw.me_full['bio'] = self.data['bio']

        self.mw.me['username'] = self.data['username']
        self.mw.me['account']['name'] = self.data['name']
        self.mw.me['account']['avatar_file_name'] = self.data['avatar_rel_path']
        self.mw.me['account']['avatar_type'] = self.data['avatar_type']

        self.mw.username = self.data['username']
        self.mw.name = self.data['name']
        self.mw.me_has_avatar = True if self.data['avatar_rel_path'] else False
        self.mw.me_avatar = self.data['avatar_rel_path']

        self.mw.profile_button.setText(self.mw.name)
        self.mw.welcome_label.setText(self.tr("Welcome back, ") + self.mw.name)

        self.mw.chat_thread.update_user_settings_2(self.data)
        self.mw.hideOverlay()
