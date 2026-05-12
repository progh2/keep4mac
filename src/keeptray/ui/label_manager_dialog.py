"""라벨 추가·편집·삭제 다이얼로그."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

from keeptray.api.keep_client import KeepClient
from keeptray.i18n import gettext as _

_CSS = """
    QDialog  { background: #ffffff; color: #1c1c1e; }
    QLabel   { color: #1c1c1e; }
    QLineEdit {
        background: #f2f2f7; border: 1px solid #d1d1d6;
        border-radius: 6px; padding: 5px 10px;
        font-size: 13px; color: #1c1c1e;
    }
    QLineEdit:focus { border-color: #007AFF; background: #ffffff; }
"""

_ROW_BTN = """
    QPushButton {
        background: transparent; border: none;
        color: #8e8e93; font-size: 13px; padding: 2px 6px;
        border-radius: 4px;
    }
    QPushButton:hover { background: #f2f2f7; color: #FF3B30; }
"""

_ADD_BTN = """
    QPushButton {
        background: #007AFF; color: white; border: none;
        border-radius: 6px; font-size: 13px; padding: 6px 14px;
    }
    QPushButton:hover { background: #0066d6; }
    QPushButton:disabled { background: #a0c4ff; }
"""


class LabelManagerDialog(QDialog):
    labels_changed = pyqtSignal()

    def __init__(self, client: KeepClient, parent=None):
        super().__init__(parent)
        self._client = client
        self.setWindowTitle(_("Label Management"))
        self.setMinimumWidth(320)
        self.setMaximumHeight(480)
        self.setStyleSheet(_CSS)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(10)

        # 라벨 목록 스크롤 영역
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet("QScrollArea { background: transparent; }")
        self._scroll.setMinimumHeight(120)
        self._scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()
        self._scroll.setWidget(self._list_widget)
        root.addWidget(self._scroll)

        # 구분선
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #e5e5ea;")
        sep.setFixedHeight(1)
        root.addWidget(sep)

        # 새 라벨 추가 행
        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        self._new_edit = QLineEdit()
        self._new_edit.setPlaceholderText(_("New label name…"))
        self._new_edit.returnPressed.connect(self._on_add)
        add_row.addWidget(self._new_edit, 1)
        self._add_btn = QPushButton(_("Add"))
        self._add_btn.setStyleSheet(_ADD_BTN)
        self._add_btn.clicked.connect(self._on_add)
        add_row.addWidget(self._add_btn)
        root.addLayout(add_row)

        # 닫기 버튼
        close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_box.setStyleSheet("color: #1c1c1e;")
        close_box.rejected.connect(self.accept)
        root.addWidget(close_box)

    def _load(self):
        """라벨 목록을 다시 불러와 행을 재구성한다."""
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        labels = self._client.get_labels()
        if not labels:
            empty = QLabel(_("No labels"))
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet("color: #8e8e93; font-size: 13px; padding: 16px;")
            self._list_layout.insertWidget(0, empty)
            return

        for i, lbl in enumerate(labels):
            row = self._make_row(lbl["id"], lbl["name"])
            self._list_layout.insertWidget(i, row)

    def _make_row(self, label_id: str, name: str) -> QWidget:
        row = QWidget()
        row.setStyleSheet("background: transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(6)

        icon = QLabel("🏷")
        icon.setStyleSheet("font-size: 14px; background: transparent;")
        rl.addWidget(icon)

        edit = QLineEdit(name)
        edit.setProperty("label_id", label_id)
        edit.editingFinished.connect(
            lambda lid=label_id, e=edit: self._on_rename(lid, e)
        )
        rl.addWidget(edit, 1)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(28, 28)
        del_btn.setStyleSheet(_ROW_BTN)
        del_btn.setToolTip(_("Delete"))
        del_btn.clicked.connect(lambda checked=False, lid=label_id, n=name: self._on_delete(lid, n))
        rl.addWidget(del_btn)

        return row

    def _on_rename(self, label_id: str, edit: QLineEdit):
        new_name = edit.text().strip()
        if not new_name:
            return
        self._client.rename_label(label_id, new_name)
        self.labels_changed.emit()

    def _on_delete(self, label_id: str, name: str):
        msg = QMessageBox(self)
        msg.setWindowTitle(_("Delete Label"))
        msg.setText(f"'{name}'\n{_('Delete this label?')}")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.button(QMessageBox.StandardButton.Yes).setText(_("Delete"))
        msg.button(QMessageBox.StandardButton.No).setText(_("Cancel"))
        if msg.exec() != QMessageBox.StandardButton.Yes:
            return
        self._client.delete_label(label_id)
        self.labels_changed.emit()
        self._load()

    def _on_add(self):
        name = self._new_edit.text().strip()
        if not name:
            return
        result = self._client.create_label(name)
        if result:
            self._new_edit.clear()
            self.labels_changed.emit()
            self._load()
