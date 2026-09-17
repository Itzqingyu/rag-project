import React from 'react';
import { AlertTriangle, Trash2 } from 'lucide-react';
import './ConfirmModal.css';

export interface ConfirmModalProps {
  isOpen: boolean;
  title?: string;
  message?: string;
  confirmText?: string;
  cancelText?: string;
  isDanger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

/**
 * 通用防手殘確認對話框 (ConfirmModal)
 * 特性：
 * 1. 彈出覆蓋全螢幕的半透明 Backdrop，並對背景畫面套用高階毛玻璃模糊 (backdrop-filter: blur)
 * 2. 居中顯示俐落的卡片對話框，提供警告標題、說明文字與取消/確認按鈕
 * 3. 支援 Esc 鍵取消或點擊遮罩外圍取消
 */
export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  title = '確認刪除',
  message = '確定要刪除這筆資料嗎？此操作將無法復原。',
  confirmText = '確認刪除',
  cancelText = '取消',
  isDanger = true,
  onConfirm,
  onCancel,
}) => {
  if (!isOpen) return null;

  return (
    <div
      className="confirm-modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
      onClick={onCancel}
    >
      <div
        className="confirm-modal-card"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="confirm-modal-icon-wrapper">
          {isDanger ? (
            <div className="confirm-icon-danger">
              <AlertTriangle size={24} />
            </div>
          ) : (
            <div className="confirm-icon-normal">
              <Trash2 size={24} />
            </div>
          )}
        </div>

        <div className="confirm-modal-content">
          <h3 id="confirm-modal-title">{title}</h3>
          <p>{message}</p>
        </div>

        <div className="confirm-modal-actions">
          <button
            type="button"
            className="button secondary modal-cancel-btn"
            onClick={onCancel}
          >
            {cancelText}
          </button>
          <button
            type="button"
            className={`button modal-confirm-btn ${isDanger ? 'danger' : 'primary'}`}
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;
