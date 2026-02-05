import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.main}>
      {/* Hero Section */}
      <section className={styles.hero}>
        <div className="animate-fade-in">
          <h1 className={styles.title}>
            Train Smarter with <br />
            <span className="text-gradient">TrueShift AI</span>
          </h1>
          <p className={styles.subtitle}>
            The workout coach that sees what you see.<br />
            Scan gym equipment. Train smarter. Recover better.
          </p>
          <a href="#download" className={styles.ctaButton}>
            Get Early Access
          </a>
        </div>
      </section>

      {/* TrueShift vision and mission */}
      <section className={styles.section}>
        <div style={{ maxWidth: "800px", textAlign: "center" }}>
          <h2 className={styles.featureTitle}>Why TrueShift Exists</h2>

          <p style={{
            fontSize: "1.4rem",
            fontWeight: 600,
            margin: "2rem 0 1rem"
          }}>
            To make intelligent, personalized training accessible to everyone.
          </p>

          <p className={styles.featureDesc}>
            TrueShift uses AI and computer vision to understand your workout environment,
            adapt training to your recovery, and help you progress safely and sustainably.
          </p>
        </div>
      </section>

      {/* Vision Feature */}
      <section className={styles.section}>
        <div className={styles.featureRow}>
          <div className={styles.featureText}>
            <h2 className={styles.featureTitle}>
              See Your Gym Smarter
            </h2>
            <p className={styles.featureDesc}>
              Point your camera at any gym machine. TrueShift recognizes it instantly and recommends exercises based on your current recovery state.
            </p>

          </div>
          <div className={`${styles.featureVisual} glass-panel animate-float`}>
            {/* Placeholder for scanning demo */}
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📸</div>
              <div style={{ color: '#6366f1', fontWeight: 'bold' }}>Simulated Scan</div>
            </div>
          </div>
        </div>
      </section>

      {/* AI Plans Feature */}
      <section className={styles.section}>
        <div className={`${styles.featureRow} ${styles.reverse}`}>
          <div className={`${styles.featureText} ${styles.reverse}`}>
            <h2 className={styles.featureTitle}>
              <span className="text-gradient-primary">Dynamic Recovery</span>
            </h2>
            <p className={styles.featureDesc}>
              Tired? We'll lighten the load. <br />
              Fresh? We'll push your limits. <br />
              Your volume adjusts automatically based on your daily recovery score.
            </p>
          </div>
          <div className={`${styles.featureVisual} glass-panel`}>
            {/* Placeholder for Plan UI */}
            <div style={{ textAlign: 'center', direction: 'ltr' }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⚡</div>
              <div style={{ color: '#10b981', fontWeight: 'bold' }}>Adaptive Volume</div>
            </div>
          </div>
        </div>
      </section>

      {/* Download / Footer */}
      <footer id="download" className={styles.footer}>
        <h3 className={styles.featureTitle} style={{ fontSize: '2rem', marginBottom: '2rem' }}>
          Ready to Shift?
        </h3>
        <a href="#" className={styles.ctaButton} style={{ background: '#333', color: '#fff', border: '1px solid #444' }}>
          Download APK (Beta)
        </a>
        <p style={{ marginTop: '4rem', fontSize: '0.9rem' }}>
          © 2026 TrueShift AI. Built with Gemini 1.5.
        </p>
      </footer>
    </main>
  );
}
