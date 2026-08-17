from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
)

from modules.ui.ThemeManager import TM
from modules.ui.elements.Buttons import PushButton
from modules.ui.elements.Menus import PushButtonMenu
from modules.ui.elements.ScrollAreas import VerticalScrollPage


class LeftSidebar(QFrame):
    def __init__(self, mw):
        super().__init__(mw)
        self.setMouseTracking(True)
        self.setObjectName("leftSidebar")
        self.resizing = False
        self.startPos = None
        self.mw = mw
        self.setFixedWidth(int(self.mw.settings.value("left_sidebar_width", 255)))

        self.initUI()
        self.resizeCards()
        if self.width() <= 100:
            self.profile_button.setVisible(False)
            self.to_main_page_button.setVisible(False)
            self.create_button.setVisible(False)
            self.profile_button_2.setVisible(True)
            self.to_main_page_button_2.setVisible(True)
            self.create_button_2.setVisible(True)
        else:
            self.profile_button.setVisible(True)
            self.to_main_page_button.setVisible(True)
            self.create_button.setVisible(True)
            self.profile_button_2.setVisible(False)
            self.to_main_page_button_2.setVisible(False)
            self.create_button_2.setVisible(False)

        TM.theme_changed.connect(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.setStyleSheet(TM.get_style("LeftSidebar"))
        self.to_main_page_button_2.setIcon(self.mw.svg_icons.discover(TM.c("icon")))
        self.create_button_2.setIcon(self.mw.svg_icons.create(TM.c("icon")))

    def initUI(self):
        self.left_sidebar_layout = QVBoxLayout()
        self.left_sidebar_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.left_sidebar_layout)

        self.buttons_layout = QHBoxLayout()
        self.left_sidebar_layout.addLayout(self.buttons_layout)

        self.to_main_page_button = PushButton(self.tr("To Main Page"))
        self.to_main_page_button.clicked.connect(self.mw.showMainPage)
        self.buttons_layout.addWidget(self.to_main_page_button, 1)

        self.to_main_page_button_2 = PushButton()
        self.to_main_page_button_2.clicked.connect(self.mw.showMainPage)
        self.buttons_layout.addWidget(self.to_main_page_button_2, 1)
        self.to_main_page_button_2.setVisible(False)

        self.create_button = PushButton(self.tr("Create"))
        self.create_button.clicked.connect(
            lambda: self.showCreateContextMenu(self.create_button)
        )
        self.left_sidebar_layout.addWidget(self.create_button)

        self.create_button_2 = PushButton()
        self.create_button_2.clicked.connect(
            lambda: self.showCreateContextMenu(self.create_button_2)
        )
        self.left_sidebar_layout.addWidget(self.create_button_2)
        self.create_button_2.setVisible(False)

        self.recent_chat_scroll_page = VerticalScrollPage()
        self.recent_chat_scroll_page.setFixedWidth(
            int(self.mw.settings.value("left_sidebar_width", 250)) - 20
        )
        self.recent_chat_scroll_viewport = self.recent_chat_scroll_page.viewport
        self.recent_chat_scroll_viewport.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        self.recent_chat_scroll_layout = self.recent_chat_scroll_page.layout
        self.recent_chat_scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_chat_scroll_layout.setSpacing(5)

        self.left_sidebar_layout.addWidget(self.recent_chat_scroll_page)

        self.bottom_button_layout = QHBoxLayout()
        self.left_sidebar_layout.addLayout(self.bottom_button_layout)

        self.profile_button = PushButton(self.tr("Profile"))
        self.profile_button.clicked.connect(
            lambda: self.showProfileContextMenu(self.profile_button)
        )
        self.bottom_button_layout.addWidget(self.profile_button, 1)

        self.profile_button_2 = PushButton()
        if self.mw.me_has_avatar:
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.mw.me_avatar}?webp=true&anim=0",
                45,
                45,
                100,
                callback=lambda pixmap: self.profile_button_2.setIcon(QIcon(pixmap)),
                error_cb=lambda _: self.profile_button_2.setIcon(
                    self.mw.svg_icons.profile(TM.c("icon"))
                ),
            )
        else:
            self.profile_button_2.setIcon(self.mw.svg_icons.profile(TM.c("icon")))
        self.profile_button_2.clicked.connect(
            lambda: self.showProfileContextMenu(self.profile_button_2)
        )
        self.bottom_button_layout.addWidget(self.profile_button_2, 1)
        self.profile_button_2.setVisible(False)

    def showCreateContextMenu(self, button: PushButton):
        context_menu = PushButtonMenu(self)
        context_menu.setFixedWidth(
            int(self.mw.settings.value("left_sidebar_width", 250)) - 20
        )

        character_action = QAction(self.tr("Character"))
        character_action.triggered.connect(self.mw.openCreateCharacterPage)
        context_menu.addAction(character_action)

        scene_action = QAction(self.tr("Scene"))
        scene_action.triggered.connect(self.mw.openCreateScenePage)
        context_menu.addAction(scene_action)

        context_menu.exec(button.mapToGlobal(QPoint(0, context_menu.height())))

    def showProfileContextMenu(self, button: PushButton):
        context_menu = PushButtonMenu(self)
        context_menu.setFixedWidth(
            int(self.mw.settings.value("left_sidebar_width", 250)) - 20
        )

        profile_action = QAction(self.tr("Profile"))
        profile_action.triggered.connect(self.openUserPage)
        context_menu.addAction(profile_action)

        settings_action = QAction(self.tr("Settings"))
        settings_action.triggered.connect(self.mw.openSettings)
        context_menu.addAction(settings_action)

        context_menu.exec(button.mapToGlobal(QPoint(0, -2 * context_menu.height())))

    def avatarUpdate(self):
        if self.mw.me_has_avatar:
            self.mw.image_loader.load(
                f"https://characterai.io/i/80/static/avatars/{self.mw.me_avatar}?webp=true&anim=0",
                45,
                45,
                100,
                callback=lambda pixmap: self.profile_button_2.setIcon(QIcon(pixmap)),
                error_cb=lambda _: self.profile_button_2.setIcon(
                    self.mw.svg_icons.profile(TM.c("icon"))
                ),
            )
        else:
            self.profile_button_2.setIcon(self.mw.svg_icons.profile(TM.c("icon")))

    def openUserPage(self):
        self.mw.openUserPage(self.mw.username)

    def resizeCards(self):
        for i in range(self.recent_chat_scroll_layout.count()):
            card = self.recent_chat_scroll_layout.itemAt(i)
            card_widget = card.widget()
            self.resizeCard(card_widget)

    def resizeCard(self, card_widget):
        card_widget.setFixedWidth(self.width() - 30)
        if card_widget.width() <= 66:
            card_widget.avatar_label.setVisible(False)
            card_widget.name_label.setVisible(False)
            card_widget.menu_button.visibility = False
            card_widget.avatar_label_2.setVisible(True)
        else:
            card_widget.avatar_label.setVisible(True)
            card_widget.name_label.setVisible(True)
            card_widget.menu_button.visibility = True
            card_widget.avatar_label_2.setVisible(False)

    def mousePressEvent(self, event):
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.cursor().shape() == Qt.CursorShape.SizeHorCursor
        ):
            self.resizing = True
            self.startPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        edge_size = 5
        frame_rect = self.rect()

        if self.resizing:
            diff_x = event.globalPosition().toPoint().x() - self.startPos.x()
            new_width = min(max(88, self.width() + diff_x), 255)
            if self.width() > 88 and new_width <= 120:
                new_width = 88
            elif self.width() == 88 and diff_x > 0:
                new_width = 121
            self.startPos = event.globalPosition().toPoint()

            self.setFixedWidth(new_width)
            self.recent_chat_scroll_page.setFixedWidth(new_width - 20)
            self.mw.settings.setValue("left_sidebar_width", new_width)
            self.resizeCards()
            if self.width() <= 120:
                self.profile_button.setVisible(False)
                self.to_main_page_button.setVisible(False)
                self.create_button.setVisible(False)
                self.profile_button_2.setVisible(True)
                self.to_main_page_button_2.setVisible(True)
                self.create_button_2.setVisible(True)
            else:
                self.profile_button.setVisible(True)
                self.to_main_page_button.setVisible(True)
                self.create_button.setVisible(True)
                self.profile_button_2.setVisible(False)
                self.to_main_page_button_2.setVisible(False)
                self.create_button_2.setVisible(False)

        else:
            if frame_rect.right() - edge_size < event.pos().x() < frame_rect.right():
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self.resizing = False
