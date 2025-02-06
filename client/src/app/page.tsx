export default function Home() {
  return (
    <main className="min-h-screen p-24">
      <h1 className="text-4xl font-bold text-center mb-8">
        🕷️ Web Crawler Dashboard
      </h1>

      <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-md p-6">
        <div className="mb-6">
          <label className="block text-gray-700 text-sm font-bold mb-2">
            Website URL
          </label>
          <input
            type="text"
            className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="https://example.com"
          />
        </div>

        <button className="w-full bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline">
          Start Crawling
        </button>

        <div className="mt-8 space-y-4">
          <div className="p-4 bg-gray-50 rounded-md">
            <h3 className="text-lg font-semibold mb-2">Crawl Progress</h3>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all"
                style={{ width: '45%' }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}