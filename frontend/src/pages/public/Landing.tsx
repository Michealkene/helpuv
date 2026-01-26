import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <div className="bg-white">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Clean B2B Lead Data,<br />No Subscription Required
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Download curated CSV datasets with verified company emails and phone numbers. 
              Pay once, own forever.
            </p>
            <div className="flex justify-center space-x-4">
              <Link
                to="/datasets"
                className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 font-semibold text-lg"
              >
                Browse Datasets
              </Link>
              <Link
                to="/auth/signup"
                className="bg-white text-blue-600 px-8 py-3 rounded-lg hover:bg-gray-50 font-semibold text-lg border-2 border-blue-600"
              >
                Get Started Free
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
        <h2 className="text-3xl font-bold text-center mb-12">Why Helpuvio?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center p-6">
            <div className="text-4xl mb-4">✓</div>
            <h3 className="text-xl font-semibold mb-2">Verified Data</h3>
            <p className="text-gray-600">
              All emails and phone numbers are validated before inclusion
            </p>
          </div>
          <div className="text-center p-6">
            <div className="text-4xl mb-4">💰</div>
            <h3 className="text-xl font-semibold mb-2">Pay Once, Own Forever</h3>
            <p className="text-gray-600">
              No subscriptions. Download your data and use it however you want
            </p>
          </div>
          <div className="text-center p-6">
            <div className="text-4xl mb-4">⚡</div>
            <h3 className="text-xl font-semibold mb-2">Instant Download</h3>
            <p className="text-gray-600">
              Get your CSV file immediately after purchase
            </p>
          </div>
        </div>
      </div>

      {/* CTA */}
      <div className="bg-blue-600 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-xl mb-8">Browse our datasets and start building your sales pipeline today</p>
          <Link
            to="/datasets"
            className="bg-white text-blue-600 px-8 py-3 rounded-lg hover:bg-gray-100 font-semibold text-lg inline-block"
          >
            View All Datasets
          </Link>
        </div>
      </div>
    </div>
  )
}