import { useState, useEffect } from 'react';
import api from '../../lib/api';
import { Link } from 'react-router-dom';
import { ShoppingCart, Search, Filter } from 'lucide-react';

interface Dataset {
  id: number;
  name: string;
  slug: string;
  description: string;
  company_count: number;
  enrichment_level: string;
  category?: { name: string; slug: string };
  location?: string;
}

interface Category {
  id: number;
  name: string;
  slug: string;
  dataset_count: number;
}

export default function Datasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchData();
  }, [selectedCategory]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [datasetsRes, categoriesRes] = await Promise.all([
        api.get('/datasets', {
          params: selectedCategory ? { category: selectedCategory } : {}
        }),
        api.get('/datasets/categories')
      ]);
      
      setDatasets(datasetsRes.data.items || []);
      // Only show categories with datasets
      setCategories(categoriesRes.data.filter((cat: Category) => cat.dataset_count > 0));
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredDatasets = datasets.filter(d =>
    d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (d.description && d.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getPriceInfo = (dataset: Dataset) => {
    const pricePerCompany = dataset.enrichment_level === 'phone_only' ? 0.05 : 0.10;
    const totalPrice = dataset.company_count * pricePerCompany;
    return {
      pricePerCompany,
      totalPrice,
      label: dataset.enrichment_level === 'phone_only' ? 'Phone Only' : 'Email & Phone'
    };
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-48 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold">Browse Datasets</h1>
        <Link
          to="/cart"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          <ShoppingCart className="h-5 w-5" />
          <span className="hidden sm:inline">Cart</span>
        </Link>
      </div>

      {/* Search & Filters */}
      <div className="mb-6 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
          <input
            type="text"
            placeholder="Search datasets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* Categories - Horizontal scroll on mobile */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">
          <Filter className="h-5 w-5 text-gray-500 flex-shrink-0" />
          <button
            onClick={() => setSelectedCategory('')}
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition ${
              !selectedCategory
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Categories
          </button>
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.slug)}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition ${
                selectedCategory === cat.slug
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {cat.name} ({cat.dataset_count})
            </button>
          ))}
        </div>
      </div>

      {/* Datasets Grid - Responsive */}
      {filteredDatasets.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-500 text-lg">No datasets found</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:gap-6 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          {filteredDatasets.map((dataset) => {
            const { pricePerCompany, totalPrice, label } = getPriceInfo(dataset);
            
            return (
              <Link
                key={dataset.id}
                to={`/datasets/${dataset.slug}`}
                className="bg-white border rounded-lg p-4 sm:p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex justify-between items-start mb-3">
                  <h3 className="text-lg sm:text-xl font-semibold pr-2 line-clamp-2">
                    {dataset.name}
                  </h3>
                  <span className={`px-2 py-1 text-xs rounded whitespace-nowrap flex-shrink-0 ${
                    dataset.enrichment_level === 'phone_only'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {label}
                  </span>
                </div>

                {dataset.description && (
                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                    {dataset.description}
                  </p>
                )}

                <div className="space-y-2">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-500">Companies</span>
                    <span className="font-semibold">{dataset.company_count.toLocaleString()}</span>
                  </div>

                  <div className="flex justify-between items-center text-sm">
                    <span className="text-gray-500">Price per company</span>
                    <span className="font-semibold">${pricePerCompany}</span>
                  </div>

                  <div className="pt-2 border-t">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Full dataset</span>
                      <span className="text-xl sm:text-2xl font-bold text-blue-600">
                        ${totalPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                    </div>
                  </div>
                </div>

                {dataset.location && (
                  <div className="mt-3 pt-3 border-t text-xs text-gray-500">
                    📍 {dataset.location}
                  </div>
                )}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
