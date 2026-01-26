export default function Privacy() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Privacy Policy</h1>
      
      <div className="prose prose-gray max-w-none">
        <p className="text-gray-600 mb-6">
          Last updated: January 2026
        </p>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">What We Collect</h2>
          <ul className="list-disc list-inside text-gray-600 space-y-2">
            <li>Your email address (for login and receipts)</li>
            <li>Your name (optional, from signup or Google OAuth)</li>
            <li>Your purchase history (so you can re-download)</li>
            <li>IP address (only for security logs, deleted after 90 days)</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">What We Don't Collect</h2>
          <ul className="list-disc list-inside text-gray-600 space-y-2">
            <li>We don't track you across websites</li>
            <li>We don't sell your email to marketers</li>
            <li>We don't use analytics cookies (only essential ones)</li>
            <li>We never store your payment card details (Paystack handles that)</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">The Data We Sell</h2>
          <p className="text-gray-600 mb-4">
            Our datasets contain publicly available business contact information. This data is sourced from public websites, directories, and business registries.
          </p>
          <p className="text-gray-600">
            If you want your company removed from our datasets, email us at{' '}
            <a href="mailto:privacy@helpuvio.com" className="text-primary-600 hover:underline">
              privacy@helpuvio.com
            </a>
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Your Rights</h2>
          <ul className="list-disc list-inside text-gray-600 space-y-2">
            <li><strong>Export your data:</strong> Go to Settings → Export Data</li>
            <li><strong>Delete your account:</strong> Go to Settings → Delete Account</li>
            <li>We'll delete everything except purchase records (required by law)</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Data Storage</h2>
          <ul className="list-disc list-inside text-gray-600 space-y-2">
            <li>Your data is stored in secure databases</li>
            <li>Payment data is handled by Paystack (PCI compliant)</li>
            <li>We use industry-standard encryption (HTTPS, bcrypt)</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Questions?</h2>
          <p className="text-gray-600">
            Email us at{' '}
            <a href="mailto:privacy@helpuvio.com" className="text-primary-600 hover:underline">
              privacy@helpuvio.com
            </a>
          </p>
        </section>
      </div>
    </div>
  )
}
