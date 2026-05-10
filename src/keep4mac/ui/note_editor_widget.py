from PyQt6.QtCore import Qt, QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QGuiApplication, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy, QTextEdit,
    QVBoxLayout, QWidget,
)

from keep4mac.api.keep_client import KeepClient
from keep4mac.core.models import COLOR_HEX, NoteColor, NoteModel, NoteType
from keep4mac.core.url_utils import extract_urls, short_url
from keep4mac.i18n import gettext as _

# 색상 팔레트 순서 (DEFAULT는 흰색 맨 앞)
_PALETTE = [
    NoteColor.DEFAULT, NoteColor.RED, NoteColor.ORANGE, NoteColor.YELLOW,
    NoteColor.GREEN, NoteColor.TEAL, NoteColor.BLUE, NoteColor.CERULEAN,
    NoteColor.PURPLE, NoteColor.PINK, NoteColor.BROWN, NoteColor.GRAY,
]


class _ImageThread(QThread):
    done = pyqtSignal(bytes)

    def __init__(self, url: str, client: KeepClient):
        super().__init__()
        self._url = url
        self._client = client

    def run(self):
        data = self._client.fetch_image(self._url)
        if data:
            self.done.emit(data)


class NoteEditorWidget(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, client: KeepClient):
        super().__init__()
        self._client = client
        self._note_id: str | None = None
        self._is_new = False
        self._is_pinned = False
        self._image_url: str | None = None
        self._current_color = NoteColor.DEFAULT
        self._color_btns: dict[NoteColor, QPushButton] = {}
        self._checklist_rows: list[tuple[QCheckBox, str]] = []
        self._img_thread: _ImageThread | None = None
        self._build_ui()

    # ── UI 구성 ───────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 헤더
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet("background: #1a73e8;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 0, 8, 0)
        hl.setSpacing(4)

        back_btn = QPushButton("←")
        back_btn.setFixedSize(32, 32)
        back_btn.setStyleSheet("""
            QPushButton { background: transparent; color: white; border: none; font-size: 16px; }
            QPushButton:hover { background: rgba(255,255,255,0.2); border-radius: 16px; }
        """)
        back_btn.clicked.connect(self._on_back)
        hl.addWidget(back_btn)

        self._header_label = QLabel(_("Edit Note"))
        self._header_label.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: white; background: transparent;"
        )
        hl.addWidget(self._header_label, 1)

        root.addWidget(header)

        # 본문
        self._body_widget = QWidget()
        self._body_widget.setStyleSheet("background: white;")
        body = self._body_widget
        bl = QVBoxLayout(body)
        bl.setContentsMargins(16, 12, 16, 12)
        bl.setSpacing(10)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText(_("Title"))
        self._title_edit.setStyleSheet("""
            QLineEdit {
                font-size: 16px; font-weight: 600; color: #202124;
                border: none; border-bottom: 1px solid #e8eaed;
                padding: 4px 0; background: transparent;
            }
        """)
        bl.addWidget(self._title_edit)

        # 텍스트 노트 편집기
        self._body_edit = QTextEdit()
        self._body_edit.setPlaceholderText(_("Enter note content…"))
        self._body_edit.setStyleSheet("""
            QTextEdit { font-size: 13px; color: #202124; border: none; background: transparent; }
        """)
        self._body_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        bl.addWidget(self._body_edit, 1)

        # 체크리스트 노트 스크롤 영역
        self._list_scroll = QScrollArea()
        self._list_scroll.setWidgetResizable(True)
        self._list_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._list_scroll.setStyleSheet("background: transparent;")
        self._list_container = QWidget()
        self._list_container.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()
        self._list_scroll.setWidget(self._list_container)
        self._list_scroll.hide()
        bl.addWidget(self._list_scroll, 1)

        # 이미지 섹션
        self._img_section = QFrame()
        self._img_section.setStyleSheet(
            "QFrame { background: #f8f9fa; border: 1px solid #e8eaed; border-radius: 8px; }"
        )
        img_l = QVBoxLayout(self._img_section)
        img_l.setContentsMargins(8, 8, 8, 8)
        img_l.setSpacing(6)

        self._img_display = QLabel()
        self._img_display.setFixedHeight(140)
        self._img_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_display.setStyleSheet("background: #e8eaed; border-radius: 6px;")
        img_l.addWidget(self._img_display)

        img_del_btn = QPushButton(_("🗑  Delete Image"))
        img_del_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #c5221f;
                border: 1px solid #c5221f; border-radius: 6px;
                font-size: 12px; padding: 4px 10px;
            }
            QPushButton:hover { background: #fce8e6; }
        """)
        img_del_btn.clicked.connect(self._on_delete_image)
        img_l.addWidget(img_del_btn, 0, Qt.AlignmentFlag.AlignRight)

        self._img_section.hide()
        bl.addWidget(self._img_section)

        # 링크 섹션
        self._links_section = QFrame()
        self._links_section.setStyleSheet(
            "QFrame { background: #f8f9fa; border: 1px solid #e8eaed; border-radius: 8px; }"
        )
        links_l = QVBoxLayout(self._links_section)
        links_l.setContentsMargins(10, 8, 10, 8)
        links_l.setSpacing(4)

        links_header = QLabel(_("🔗 Links"))
        links_header.setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #5f6368; background: transparent;"
        )
        links_l.addWidget(links_header)

        self._links_body = QVBoxLayout()
        self._links_body.setSpacing(2)
        links_l.addLayout(self._links_body)

        self._links_section.hide()
        bl.addWidget(self._links_section)

        root.addWidget(body, 1)

        # 하단 footer (색상 팔레트 2행 + 저장 버튼)
        self._footer_widget = QWidget()
        footer = self._footer_widget
        footer.setFixedHeight(64)
        footer.setStyleSheet("background: white; border-top: 1px solid #e8eaed;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(12, 8, 12, 8)
        fl.setSpacing(8)

        # 색상 팔레트 6×2 그리드
        palette_col = QVBoxLayout()
        palette_col.setSpacing(4)
        row1, row2 = _PALETTE[:6], _PALETTE[6:]
        for row_colors in (row1, row2):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(4)
            row_layout.setContentsMargins(0, 0, 0, 0)
            for color in row_colors:
                btn = QPushButton()
                btn.setFixedSize(20, 20)
                btn.setCheckable(True)
                btn.clicked.connect(lambda _, c=color: self._on_color_pick(c))
                self._color_btns[color] = btn
                row_layout.addWidget(btn)
            palette_col.addLayout(row_layout)

        fl.addLayout(palette_col)

        # 핀 고정 토글 버튼
        self._pin_btn = QPushButton("📌")
        self._pin_btn.setFixedSize(32, 32)
        self._pin_btn.setCheckable(True)
        self._pin_btn.setToolTip(_("Pin / Unpin"))
        self._pin_btn.clicked.connect(self._on_pin_toggle)
        fl.addWidget(self._pin_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self._delete_btn = QPushButton("✕")
        self._delete_btn.setFixedSize(32, 32)
        self._delete_btn.setToolTip(_("Delete"))
        self._delete_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #c5221f;
                border: 1.5px solid #c5221f; border-radius: 8px;
                font-size: 15px; font-weight: 600;
            }
            QPushButton:hover { background: #fce8e6; }
            QPushButton:pressed { background: #f5c6c5; }
        """)
        self._delete_btn.clicked.connect(self._on_delete)
        fl.addWidget(self._delete_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        fl.addStretch()
        self._refresh_palette()
        self._refresh_pin_btn()

        self._save_btn = QPushButton(_("Save"))
        self._save_btn.setMinimumWidth(80)
        self._save_btn.setStyleSheet("""
            QPushButton {
                background: #1a73e8; color: white;
                border: none; border-radius: 6px;
                padding: 6px 16px; font-size: 13px; font-weight: 500;
            }
            QPushButton:hover { background: #1557b0; }
            QPushButton:pressed { background: #0d47a1; }
        """)
        self._save_btn.clicked.connect(self._on_save)
        fl.addWidget(self._save_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        root.addWidget(footer)

    # ── 공개 API ──────────────────────────────────────────────

    def retranslate_ui(self):
        self._title_edit.setPlaceholderText(_("Title"))
        self._body_edit.setPlaceholderText(_("Enter note content…"))
        self._delete_btn.setToolTip(_("Delete"))
        self._pin_btn.setToolTip(_("Pin / Unpin"))
        self._save_btn.setText(_("Save"))
        if self._is_new:
            self._header_label.setText(_("New Note"))
        else:
            self._header_label.setText(_("Edit Note"))

    def load_note(self, note_id: str):
        note = self._client.get_note(note_id)
        if not note:
            self.back_requested.emit()
            return
        self._note_id = note_id
        self._is_new = False
        self._header_label.setText(_("Edit Note"))
        self._delete_btn.show()
        self._populate(note)

    def new_note(self):
        self._note_id = None
        self._is_new = True
        self._image_url = None
        self._is_pinned = False
        self._header_label.setText(_("New Note"))
        self._delete_btn.hide()
        self._title_edit.clear()
        self._body_edit.clear()
        self._body_edit.show()
        self._list_scroll.hide()
        self._checklist_rows.clear()
        self._img_section.hide()
        self._links_section.hide()
        self._set_color(NoteColor.DEFAULT)
        self._refresh_pin_btn()
        self._title_edit.setFocus()

    # ── 내부 ──────────────────────────────────────────────────

    def _populate(self, note: NoteModel):
        self._image_url = note.image_url
        self._is_pinned = note.pinned
        self._title_edit.setText(note.title)
        self._set_color(note.color)
        self._refresh_pin_btn()

        if note.note_type == NoteType.LIST:
            self._body_edit.hide()
            self._list_scroll.show()
            self._rebuild_checklist(note)
            all_text = " ".join(i.text for i in note.checklist_items)
        else:
            self._list_scroll.hide()
            self._body_edit.show()
            self._body_edit.setPlainText(note.text)
            all_text = note.text

        self._update_image(note.image_url)
        self._update_links(all_text)

    def _rebuild_checklist(self, note: NoteModel):
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._checklist_rows.clear()

        for ci in note.checklist_items:
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(8)

            cb = QCheckBox()
            cb.setChecked(ci.checked)
            rl.addWidget(cb)

            lbl = QLabel(ci.text)
            lbl.setStyleSheet("font-size: 13px; color: #202124; background: transparent;")
            lbl.setWordWrap(True)
            rl.addWidget(lbl, 1)

            self._list_layout.insertWidget(self._list_layout.count() - 1, row)
            self._checklist_rows.append((cb, ci.text))

    def _update_image(self, image_url: str | None):
        if not image_url:
            self._img_section.hide()
            return
        self._img_display.clear()
        self._img_display.setText(_("Loading image…"))
        self._img_section.show()

        self._img_thread = _ImageThread(image_url, self._client)
        self._img_thread.done.connect(self._on_image_ready)
        self._img_thread.start()

    def _on_image_ready(self, data: bytes):
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        if pixmap.isNull():
            return
        w = self._img_display.width() or 280
        h = self._img_display.height()
        scaled = pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)
        self._img_display.setText("")
        self._img_display.setPixmap(scaled)

    def _update_links(self, text: str):
        # 기존 링크 위젯 제거
        while self._links_body.count():
            item = self._links_body.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        urls = extract_urls(text)
        if not urls:
            self._links_section.hide()
            return

        for url in urls:
            display = short_url(url, 45)
            lbl = QLabel(f'<a href="{url}" style="color:#1a73e8;">{display}</a>')
            lbl.setOpenExternalLinks(True)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size: 12px; background: transparent;")
            self._links_body.addWidget(lbl)

        self._links_section.show()

    # ── 슬롯 ──────────────────────────────────────────────────

    def _on_back(self):
        self.back_requested.emit()

    def _on_pin_toggle(self):
        if self._is_new:
            # 새 노트는 저장 시 반영 — 버튼 상태만 업데이트
            self._is_pinned = not self._is_pinned
        else:
            # 기존 노트는 즉시 저장
            self._is_pinned = self._client.toggle_pin(self._note_id)
        self._refresh_pin_btn()

    def _refresh_pin_btn(self):
        self._pin_btn.setChecked(self._is_pinned)
        if self._is_pinned:
            self._pin_btn.setStyleSheet("""
                QPushButton {
                    background: #e8f0fe; border: 1.5px solid #1a73e8;
                    border-radius: 8px; font-size: 15px;
                }
                QPushButton:hover { background: #d2e3fc; }
            """)
        else:
            self._pin_btn.setStyleSheet("""
                QPushButton {
                    background: transparent; border: 1px solid #dadce0;
                    border-radius: 8px; font-size: 15px; color: #9aa0a6;
                }
                QPushButton:hover { background: #f1f3f4; border-color: #9aa0a6; }
            """)

    def _on_color_pick(self, color: NoteColor):
        self._set_color(color)

    def _set_color(self, color: NoteColor):
        self._current_color = color
        self._refresh_palette()
        self._apply_bg(color)

    def _refresh_palette(self):
        for color, btn in self._color_btns.items():
            hex_color = COLOR_HEX[color]
            is_selected = (color == self._current_color)
            check = "✓" if is_selected else ""
            border = "2px solid #202124" if is_selected else "1px solid rgba(0,0,0,0.2)"
            btn.setText(check)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {hex_color};
                    border: {border};
                    border-radius: 11px;
                    font-size: 11px;
                    color: #202124;
                }}
                QPushButton:hover {{ border: 2px solid rgba(0,0,0,0.4); }}
            """)

    def _apply_bg(self, color: NoteColor):
        hex_color = COLOR_HEX[color]
        self._body_widget.setStyleSheet(f"background: {hex_color};")
        self._footer_widget.setStyleSheet(
            f"background: {hex_color}; border-top: 1px solid #e8eaed;"
        )

    def _on_save(self):
        # 한글 등 IME 조합 중인 마지막 글자를 강제 확정 후 읽기
        QGuiApplication.inputMethod().commit()
        title = self._title_edit.text().strip()
        color = self._current_color
        if self._is_new:
            self._client.create_note(title, self._body_edit.toPlainText(), color, self._is_pinned)
        elif self._note_id:
            if self._list_scroll.isVisible():
                items = [(text, cb.isChecked()) for cb, text in self._checklist_rows]
                self._client.update_checklist(self._note_id, title, items, color)
            else:
                self._client.update_note(self._note_id, title, self._body_edit.toPlainText(), color)
        self.back_requested.emit()

    def _on_delete(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(_("Delete Note"))
        msg.setText(_("Are you sure you want to delete this note?\nThis action cannot be undone."))
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText(_("Delete"))
        msg.button(QMessageBox.StandardButton.No).setText(_("Cancel"))
        if msg.exec() != QMessageBox.StandardButton.Yes:
            return
        if self._note_id:
            self._client.delete_note(self._note_id)
        self.back_requested.emit()

    def _on_delete_image(self):
        if self._note_id and self._image_url:
            self._client.delete_image(self._note_id, self._image_url)
            self._image_url = None
            self._img_section.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self._on_back()
        super().keyPressEvent(event)
