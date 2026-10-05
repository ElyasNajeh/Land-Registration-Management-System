import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

export default function Modal({ title, children, onClose, wide = false }) {
  const closeRef = useRef(null);
  useEffect(() => {
    const listener = (event) => event.key === "Escape" && onClose();
    document.addEventListener("keydown", listener);
    closeRef.current?.focus();
    return () => document.removeEventListener("keydown", listener);
  }, [onClose]);
  return createPortal(<div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && onClose()}><article className={`modal ${wide ? "wide" : ""}`} role="dialog" aria-modal="true" aria-label={title}><header className="modal-header"><h2>{title}</h2><button ref={closeRef} className="modal-close" onClick={onClose} aria-label="Close modal">×</button></header><div className="modal-body">{children}</div></article></div>, document.body);
}
