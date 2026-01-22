export default function Privacy() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
      
      <div className="prose prose-lg">
        <h2>What We Collect</h2>
        <ul>
          <li>Your email (for login and receipts)</li>
          <li>Your purchases (so you can re-download)</li>
          <li>Your IP address (only for security logs, deleted after 90 days)</li>
        </ul>

        <h2>What We DON'T Collect</h2>
        <ul>
          <li>We don't track you across websites</li>
          <li>We don't sell your email to marketers</li>
          <li>We don't use analytics cookies (only essential ones)</li>
        </ul>

        <h2>The Data We Sell</h2>
        <p>
          Our datasets contain publicly available business contact information.
          This data is sourced from public websites and directories.
          If you want your company removed from our datasets, email us at privacy@helpuvio.com
        </p>

        <h2>Your Rights</h2>
        <ul>
          <li>Export your data: Go to Settings → Export Data</li>
          <li>Delete your account: Go to Settings → Delete Account</li>
          <li>We'll delete everything except purchase records (required by law)</li>
        </ul>

        <h2>Data Storage</h2>
        <ul>
          <li>Your data is stored in secure databases (PostgreSQL)</li>
          <li>Payment data is handled by Paystack (PCI compliant)</li>
          <li>We use industry-standard encryption (HTTPS, bcrypt)</li>
        </ul>

        <h2>Questions?</h2>
        <p>Email: privacy@helpuvio.com</p>
      </div>
    </div>
  )
}
