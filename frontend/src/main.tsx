import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

function isMonacoCancellation(reason: unknown) {
  if (!reason || typeof reason !== 'object') {
    return false;
  }

  const cancellation = reason as { type?: unknown; msg?: unknown };
  return cancellation.type === 'cancelation' && cancellation.msg === 'operation is manually canceled';
}

window.addEventListener('unhandledrejection', (event) => {
  // Monaco가 화면 전환 중 정상 취소한 작업은 브라우저 오류로 올리지 않는다.
  if (isMonacoCancellation(event.reason)) {
    event.preventDefault();
  }
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
