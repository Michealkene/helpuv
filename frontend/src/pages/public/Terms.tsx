export default function Terms() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Terms of Service</h1>
      
      <div className="prose prose-gray max-w-none">
        <p className="text-gray-600 mb-6">
          Last updated: January 2026
        </p>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">1. What We Provide</h2>
          <p className="text-gray-600">
            Helpuvio sells downloadable CSV datasets containing business contact information, including company names, phone numbers, email addresses, and related business data.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">2. Your Responsibilities</h2>
          
          <h3 className="text-lg font-medium text-gray-900 mt-4 mb-2">Data Usage</h3>
          <ul className="list-disc list-inside text-gray-600 space-y-2">
            <li>You are responsible for how you use the data you purchase</li>
            <li>You must comply with applicable laws (CAN-SPAM, GDPR, CASL)</li>
            <li>We are NOT liable for your marketing practices</li>
          </ul>

          <h3 className="text-lg font-medium text-gray-900 mt-4 mb-2">Account Security</h3>
          <ul className="list-disc list-inside text-gray-600 space-y-2">
            <li>Keep your password secure</li>
            <li>Don't share your account</li>
            <li>Notify us if your account is compromised</li>
          </ul>

          <h3 className="text-lg font-medium text-gray-900 mt-4 mb-2">Prohibited Uses</h3>
          <ul className="list-disc list-inside text-gray-600 space-y-2">
            <li>You may NOT resell our datasets to third parties</li>
            <li>You may use the data for your own business purposes only</li>
            <li>Bulk downloading for resale will result in account termination</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">3. Data Accuracy</h2>
          <ul className="list-disc list-inside text-gray-600 space-y-2">
            <li>We strive for accuracy but cannot guarantee 100% accuracy</li>
            <li>Email addresses and phone numbers may become outdated</li>
            <li>Verify critical contacts before use</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">4. Refund Policy</h2>
          <ul className="list-disc list-inside text-gray-600 space-y-2">
            <li>7-day money-back guarantee if data quality is unsatisfactory</li>
            <li>Refunds are at our discretion</li>
            <li>Abuse of refund policy will result in account termination</li>
          </ul>
          <p className="text-gray-600 mt-4">
            To request a refund, email{' '}
            <a href="mailto:support@helpuvio.com" className="text-primary-600 hover:underline">
              support@helpuvio.com
            </a>
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">5. What We Don't Do</h2>
          <ul className="list-disc list-inside text-gray-600 space-y-2">
            <li>We don't verify employment (contact titles may be outdated)</li>
            <li>We don't validate emails in real-time (some may bounce)</li>
            <li>We don't guarantee response rates</li>
            <li>We don't provide legal advice</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">6. Intellectual Property</h2>
          <p className="text-gray-600">
            Our datasets are compiled from publicly available information. Upon purchase, you receive a license to use the data for your own business purposes. You do not acquire ownership of the data.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">7. Limitation of Liability</h2>
          <p className="text-gray-600">
            Helpuvio is provided "as is" without warranties. We are not liable for any damages arising from your use of our datasets or services.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">8. Changes to Terms</h2>
          <p className="text-gray-600">
            We may update these terms from time to time. Continued use of Helpuvio after changes constitutes acceptance of the new terms.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Contact</h2>
          <p className="text-gray-600">
            Questions? Email us at{' '}
            <a href="mailto:legal@helpuvio.com" className="text-primary-600 hover:underline">
              legal@helpuvio.com
            </a>
          </p>
        </section>
      </div>
    </div>
  )
}
