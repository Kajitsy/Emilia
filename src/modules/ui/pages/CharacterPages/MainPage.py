from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget, QApplication

from modules.ui.Elements import PushButton, VerticalScrollPage
from modules.Utils import format_number, color_avatar
from modules.ui.cards.CharacterCards import ListCard

class MainPage(QWidget):
    def __init__(self, main_window, short_id=None, character_id=None):
        super().__init__()
        self.setStyleSheet("background-color: transparent; border: none;")
        self.mw = main_window
        self.image_loader = main_window.image_loader
        self.chat_thread = self.mw.chat_thread
        self.short_id = short_id
        self.character_id = character_id
        self.character_name = None
        self.data = {}

        self.top_bar, self.top_bar_layout = self.createTopBar()
        self.initUI()

        self.chat_thread.get_char_signal.connect(self._getCharacter)
        self.chat_thread.get_character(self.character_id, self.short_id)

    def initUI(self):
        main_layout = QHBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        fhs_page = VerticalScrollPage()
        fhs_page.setStyleSheet("background-color: transparent; border: none;")
        fhs_page.setFixedWidth(400)
        fhs_layout = fhs_page.layout

        self.display_avatar = QLabel()
        self.display_avatar.setFixedSize(120, 120)
        fhs_layout.addWidget(self.display_avatar)

        self.character_name_label = QLabel()
        hg_font = self.character_name_label.font()
        hg_font.setBold(True)
        hg_font.setPointSize(14)
        self.character_name_label.setFont(hg_font)
        self.character_name_label.setWordWrap(True)
        fhs_layout.addWidget(self.character_name_label)

        self.author_label = QLabel()
        self.author_label.setStyleSheet("color: #a2a2ac;")
        font = self.author_label.font()
        font.setBold(True)
        font.setPointSize(10)
        self.author_label.setFont(font)
        self.author_label.setWordWrap(True)
        fhs_layout.addWidget(self.author_label)
        self.author_label.setVisible(False)

        but_layout = QHBoxLayout()
        fhs_layout.addLayout(but_layout)

        self.chat_button = PushButton(self.tr("Chat"))
        self.chat_button.clicked.connect(lambda: self.mw.openChat(self.character_id, self.character_name))
        but_layout.addWidget(self.chat_button, 1)

        self.like_button = PushButton()
        self.like_button.setIcon(self.mw.svg_icons.like())
        self.like_button.clicked.connect(self.likeCharacter)
        but_layout.addWidget(self.like_button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.dislike_button = PushButton()
        self.dislike_button.setIcon(self.mw.svg_icons.dislike())
        self.dislike_button.clicked.connect(self.dislikeCharacter)
        but_layout.addWidget(self.dislike_button, 0, Qt.AlignmentFlag.AlignHCenter)

        self.share_button = PushButton()
        self.share_button.setIcon(self.mw.svg_icons.share())
        self.share_button.clicked.connect(self.shareCharacter)
        but_layout.addWidget(self.share_button, 0, Qt.AlignmentFlag.AlignRight)

        cl_layout = QHBoxLayout()
        cl_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        fhs_layout.addLayout(cl_layout)
        self.chats_label = QLabel(self.tr("0 chats"))
        sc_font = self.chats_label.font()
        sc_font.setBold(True)
        sc_font.setPointSize(10)
        self.chats_label.setFont(sc_font)
        cl_layout.addWidget(self.chats_label)
        self.span_label = QLabel("|")
        self.span_label.setFont(sc_font)
        cl_layout.addWidget(self.span_label)
        self.likes_label = QLabel(self.tr("0 likes"))
        self.likes_label.setFont(sc_font)
        cl_layout.addWidget(self.likes_label)

        self.description_label = QLabel("")
        self.description_label.setStyleSheet("color: #a2a2ac;")
        self.description_label.setFont(hg_font)
        self.description_label.setWordWrap(True)
        fhs_layout.addWidget(self.description_label, 1, alignment=Qt.AlignmentFlag.AlignTop)

        shs_page = VerticalScrollPage()
        shs_page.setStyleSheet("background-color: transparent; border: none;")
        shs_page.setFixedWidth(400)
        shs_layout = shs_page.layout

        self.simchars_label = QLabel(self.tr("Similar characters"))
        self.simchars_label.setFont(hg_font)
        shs_layout.addWidget(self.simchars_label)

        simchars_page = VerticalScrollPage()
        self.simchars_layout = simchars_page.layout
        shs_layout.addWidget(simchars_page)

        main_layout.addWidget(fhs_page)
        main_layout.addWidget(shs_page)

        self.setLayout(main_layout)

    def createTopBar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(0)
        top_bar_layout = QHBoxLayout()
        top_bar.setLayout(top_bar_layout)

        return top_bar, top_bar_layout

    def _getSimChars(self, data):
        self.chat_thread.get_recommend_chars_by_id_signal.disconnect()
        for char in data:
            card = ListCard(self.mw, char)
            card.setFixedHeight(80)
            self.simchars_layout.addWidget(card)

    def _getCharacter(self, data):
        self.chat_thread.get_char_signal.disconnect()
        self.data = data['character']
        self.character_id = self.data.get('external_id')
        self.short_id = self.data.get('short_hash')
        self.character_name = self.data['name']
        self.chat_thread.get_recommend_chars_by_id_signal.connect(self._getSimChars)
        self.chat_thread.get_recommend_chars_by_id(self.character_id)
        self.voted = data.get('voted', {}).get('voted', False)
        self.vote = data.get('voted', {}).get('vote', None)
        self.character_name_label.setText(self.character_name)
        if self.data.get('avatar_file_name'):
            self.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.data.get('avatar_file_name')}?webp=true&anim=0", 120, 120, 100,
                label=self.display_avatar,
                error_cb=lambda _: color_avatar(self.display_avatar, 120, 120, self.mw.name))
        else:
            color_avatar(self.display_avatar, 120, 120, self.character_name)
        if self.data.get('user__username'):
            self.author_label.setText(self.tr("Author: @") + self.data.get('user__username'))
            self.author_label.setVisible(True)
            self.author_label.mousePressEvent = lambda x: self.mw.openUserPage(self.data.get('user__username'))
            self.author_label.setCursor(Qt.CursorShape.PointingHandCursor)
        if self.data.get('participant__num_interactions'):
            self.chats_label.setText(format_number(self.data.get('participant__num_interactions', 0)) + self.tr(" chats"))
            self.chats_label.setVisible(True)
        if self.data.get('upvotes'):
            self.likes_label.setText(format_number(self.data.get('upvotes', '0')) + self.tr(" likes"))
            self.likes_label.setVisible(True)
        if self.data.get('description'):
            self.description_label.setText(self.data.get('description'))
        if self.voted:
            if self.vote == True:
                self.like_button.setIcon(self.mw.svg_icons.liked())
            elif self.vote == False:
                self.dislike_button.setIcon(self.mw.svg_icons.disliked())

    def shareCharacter(self):
        QApplication.clipboard().setText(f'https://character.ai/character/{self.short_id}')
        self.mw.showNotification(self.tr("Link copied to clipboard"))

    def dislikeCharacter(self):
        self.like_button.setIcon(self.mw.svg_icons.like())
        if self.vote == False:
            self.vote = None
            self.chat_thread.character_vote(self.character_id, None)
            self.dislike_button.setIcon(self.mw.svg_icons.dislike())
        else:
            self.vote = False
            self.chat_thread.character_vote(self.character_id, False)
            self.dislike_button.setIcon(self.mw.svg_icons.disliked())

    def likeCharacter(self):
        self.dislike_button.setIcon(self.mw.svg_icons.dislike())
        if self.vote:
            self.vote = None
            self.chat_thread.character_vote(self.character_id, None)
            self.like_button.setIcon(self.mw.svg_icons.like())
        else:
            self.vote = True
            self.chat_thread.character_vote(self.character_id, True)
            self.like_button.setIcon(self.mw.svg_icons.liked())

    def showEvent(self, event):
        super().showEvent(event)
        self.mw.top_bar_stacked_widget.setFixedHeight(0)
        self.mw.top_bar_stacked_widget.addWidget(self.top_bar)
        self.mw.top_bar_stacked_widget.setCurrentWidget(self.top_bar)

    def hideEvent(self, event):
        super().hideEvent(event)
        self.deleteLater()