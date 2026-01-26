import { Link } from 'react-router-dom'
import { ArrowRight, Download, Shield, Zap } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

export default function Landing() {
  const { isAuthenticated } = useAuthStore()

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-gray-50 to-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              B2B Lead Data,
              <br />
              <span className="text-primary-600">Without the Subscription</span>
            </h1>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto mb-8">
              Clean company contact datasets with verified phone numbers and emails.
              Pay once, download instantly. No monthly fees.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/datasets" className="btn btn-primary btn-lg">
                Browse Datasets
                <ArrowRight className="w-5 h-5 ml-2" />
              </Link>
              {!isAuthenticated && (
                <Link to="/signup" className="btn btn-outline btn-lg">
                  Create Free Account
                </Link>
              )}
              {isAuthenticated && (
                <Link to="/downloads" className="btn btn-outline btn-lg">
                  My Downloads
                </Link>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why Choose Helpuvio?
            </h2>
            <p className="text-gray-600 max-w-2xl mx-auto">
              We're different from expensive subscription services. 
              Get exactly what you need, when you need it.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center p-6">
              <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Zap className="w-6 h-6 text-primary-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Instant Download
              </h3>
              <p className="text-gray-600">
                Get your CSV file immediately after purchase. No waiting, no processing delays.
              </p>
            </div>

            <div className="text-center p-6">
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Shield className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Verified Data
              </h3>
              <p className="text-gray-600">
                Phone numbers and emails are verified. Get clean data that actually works.
              </p>
            </div>

            <div className="text-center p-6">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <Download className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Unlimited Re-downloads
              </h3>
              <p className="text-gray-600">
                Lost your file? Download it again anytime. No extra charges, no expiration.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-gray-600">
              Get your data in three simple steps
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-lg p-8 text-center">
              <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                1
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Browse & Select
              </h3>
              <p className="text-gray-600">
                Find the dataset that matches your needs. Preview sample data before buying.
              </p>
            </div>

            <div className="bg-white rounded-lg p-8 text-center">
              <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                2
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Purchase
              </h3>
              <p className="text-gray-600">
                Secure payment via Paystack. Pay once, no recurring charges.
              </p>
            </div>

            <div className="bg-white rounded-lg p-8 text-center">
              <div className="w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                3
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Download
              </h3>
              <p className="text-gray-600">
                Get your CSV instantly. Re-download anytime from your dashboard.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Browse our collection of verified B2B lead datasets
          </p>
          <Link to="/datasets" className="btn btn-primary btn-lg">
            View All Datasets
            <ArrowRight className="w-5 h-5 ml-2" />
          </Link>
        </div>
      </section>
    </div>
  )
}