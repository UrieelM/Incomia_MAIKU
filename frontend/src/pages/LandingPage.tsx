import { useNavigate } from 'react-router-dom';

import './LandingPage.css';

export function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="landing-wrapper">
      <header className="global-header">
        <div className="header-container">
          <div className="logo-area">
            {/* @ts-ignore */}
            <ion-icon name="flame"></ion-icon>
            <span className="brand-name">Banco</span>
          </div>
          
          <div className="header-tools">
            <div className="user-greeting">
              <span>Bienvenido, <strong>Juan P.</strong></span>
              <span className="last-login">Último acceso: 08/Abr/2026 14:22</span>
            </div>
            {/* @ts-ignore */}
            <button className="icon-action"><ion-icon name="mail-outline"></ion-icon></button>
            {/* @ts-ignore */}
            <button className="icon-action"><ion-icon name="settings-outline"></ion-icon></button>
            <button className="btn-logout" onClick={() => navigate('/login')}>Cerrar sesión</button>
            
            {/* INCOMIA Plugin Extension */}
            <button className="plugin-incomia" onClick={() => navigate('/login')}>
              INCOMIA
            </button>
          </div>
        </div>
      </header>

      <nav className="main-nav">
        <div className="nav-container">
          <a href="#" className="nav-link active">Posición Global</a>
          <a href="#" className="nav-link">Cuentas</a>
          <a href="#" className="nav-link">Tarjetas</a>
          <a href="#" className="nav-link">Transferencias y Pagos</a>
          <a href="#" className="nav-link">Inversiones</a>
          <a href="#" className="nav-link">Ofertas para ti</a>
        </div>
      </nav>

      <main className="dashboard-wrapper">
        <div className="dashboard-grid">
          <div className="products-column">
            <section className="product-group">
              <div className="group-header">
                <h2>Cuentas</h2>
                <span className="total-group-balance">$ 124,500.00 MXN</span>
              </div>
              
              <div className="product-card">
                <div className="product-info">
                  <h3 className="product-name">Súper Cuenta Nómina</h3>
                  <span className="product-number">**** **** **** 1234</span>
                </div>
                <div className="product-balance">
                  <span className="balance-amount">$ 110,250.00</span>
                  <span className="balance-label">Saldo disponible</span>
                </div>
                <div className="product-actions">
                  <a href="#">Movimientos</a> | <a href="#">Transferir</a>
                </div>
              </div>

              <div className="product-card">
                <div className="product-info">
                  <h3 className="product-name">Cuenta Ahorro Inversión</h3>
                  <span className="product-number">**** **** **** 5678</span>
                </div>
                <div className="product-balance">
                  <span className="balance-amount">$ 14,250.00</span>
                  <span className="balance-label">Saldo disponible</span>
                </div>
                <div className="product-actions">
                  <a href="#">Movimientos</a> | <a href="#">Abonar</a>
                </div>
              </div>
            </section>

            <section className="product-group">
              <div className="group-header">
                <h2>Tarjetas de Crédito</h2>
              </div>
              
              <div className="product-card credit-card">
                <div className="product-info">
                  <h3 className="product-name">Tarjeta Crédito LikeU</h3>
                  <span className="product-number">**** **** **** 9012</span>
                </div>
                <div className="product-balance">
                  <span className="balance-label">Límite de crédito: $ 50,000.00</span>
                  <span className="balance-amount negative">$ 8,450.50</span>
                  <span className="balance-label">Saldo dispuesto</span>
                </div>
                <div className="product-actions">
                  <a href="#">Pagar tarjeta</a> | <a href="#">Estado de cuenta</a>
                </div>
              </div>
            </section>
          </div>

          <div className="side-column">
            <div className="widget">
              <h3>Atajos Rápidos</h3>
              <ul className="shortcut-list">
                {/* @ts-ignore */}
                <li><ion-icon name="swap-horizontal-outline"></ion-icon> <a href="#">Transferir a terceros</a></li>
                {/* @ts-ignore */}
                <li><ion-icon name="barcode-outline"></ion-icon> <a href="#">Pago de servicios</a></li>
                {/* @ts-ignore */}
                <li><ion-icon name="phone-portrait-outline"></ion-icon> <a href="#">Recarga de celular</a></li>
                {/* @ts-ignore */}
                <li><ion-icon name="document-text-outline"></ion-icon> <a href="#">Constancia de intereses</a></li>
              </ul>
            </div>
            
            <div className="promo-widget">
              <div className="promo-content">
                <h4>Aprovecha tu Pre-Autorizado</h4>
                <p>Tienes un crédito personal de hasta <strong>$150,000 MXN</strong> a tasa preferencial.</p>
                <button className="btn-promo">Ver oferta</button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
