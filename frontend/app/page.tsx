"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [locations, setLocations] = useState<string[]>([]);
  const [cuisines, setCuisines] = useState<string[]>([]);
  
  const [selectedLocation, setSelectedLocation] = useState("");
  const [selectedBudget, setSelectedBudget] = useState("Medium");
  const [selectedCuisines, setSelectedCuisines] = useState<string[]>([]);
  const [minRating, setMinRating] = useState(4.0);
  const [additionalContext, setAdditionalContext] = useState("");

  const [showAllCuisines, setShowAllCuisines] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<any>(null);
  const [error, setError] = useState("");

  // Budget definitions with price ranges
  const budgets = [
    { label: "Low", range: "< ₹500" },
    { label: "Medium", range: "₹500–1.5k" },
    { label: "High", range: "> ₹1.5k" },
  ];

  // Fetch initial data
  useEffect(() => {
    async function fetchData() {
      try {
        const [locRes, cuiRes] = await Promise.all([
          fetch("http://localhost:8000/api/locations"),
          fetch("http://localhost:8000/api/cuisines")
        ]);
        if (locRes.ok) {
          const locData = await locRes.json();
          setLocations(locData.locations || []);
          if (locData.locations?.length > 0) setSelectedLocation(locData.locations[0]);
        }
        if (cuiRes.ok) {
          const cuiData = await cuiRes.json();
          setCuisines(cuiData.cuisines || []);
        }
      } catch (err) {
        console.error("Error fetching initial data", err);
      }
    }
    fetchData();
  }, []);

  const toggleCuisine = (cuisine: string) => {
    setSelectedCuisines(prev => 
      prev.includes(cuisine) ? prev.filter(c => c !== cuisine) : [...prev, cuisine]
    );
  };

  const handleRecommend = async () => {
    setIsLoading(true);
    setError("");
    setRecommendations(null);
    try {
      const payload = {
        location: selectedLocation,
        budget: selectedBudget.toLowerCase(),
        cuisine: selectedCuisines.length > 0 ? selectedCuisines.join(", ") : "North Indian",
        min_rating: minRating,
        preferences: additionalContext || undefined
      };

      const res = await fetch("http://localhost:8000/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      
      if (!res.ok) {
        throw new Error("Failed to fetch recommendations");
      }
      
      const data = await res.json();
      setRecommendations(data);
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <nav className="flex justify-between items-center px-4 md:px-6 h-16 w-full bg-background/80 backdrop-blur-xl docked full-width top-0 sticky z-50 border-b border-white/10 shadow-md">
        <div className="flex items-center gap-4">
          <span className="font-headline-lg-mobile md:font-headline-lg text-headline-lg-mobile md:text-headline-lg text-primary tracking-tighter drop-shadow-[0_0_10px_rgba(255,179,177,0.4)] hidden sm:block">Zomato AI</span>
        </div>
        <div className="flex items-center gap-6">
          <div className="hidden md:flex gap-6 items-center">
            <a className="text-on-surface-variant font-body-lg text-body-lg hover:text-primary transition-colors" href="#">Discover</a>
            <a className="text-primary font-bold font-body-lg text-body-lg hover:text-primary transition-colors" href="#">AI Picks</a>
            <a className="text-on-surface-variant font-body-lg text-body-lg hover:text-primary transition-colors" href="#">Saved</a>
          </div>
          <button className="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center hover:text-primary transition-colors border border-white/10">
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 0" }}>person</span>
          </button>
        </div>
      </nav>

      <main className="flex-1 max-w-[1280px] mx-auto w-full px-4 md:px-6 py-6 md:py-8 flex flex-col md:flex-row gap-6 md:gap-8">
        {/* Left Sidebar */}
        <aside className="w-full md:w-3/12 lg:w-[30%] flex-shrink-0">
          <div className="glass-panel rounded-xl p-6 sticky top-24">
            <h2 className="font-title-md text-title-md text-white mb-6 flex items-center gap-2 border-b border-white/10 pb-4">
              <span className="material-symbols-outlined text-primary">tune</span>
              Preferences
            </h2>
            <form className="space-y-6">
              <div>
                <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2">Location</label>
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">location_on</span>
                  <select 
                    className="w-full bg-surface text-white border border-white/10 rounded-lg py-2.5 pl-10 pr-4 focus:ring-1 focus:ring-zomato-red focus:border-zomato-red appearance-none font-body-sm text-body-sm"
                    value={selectedLocation}
                    onChange={(e) => setSelectedLocation(e.target.value)}
                  >
                    {locations.map(loc => (
                      <option key={loc} value={loc}>{loc}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2">Budget (For Two)</label>
                <div className="grid grid-cols-3 gap-2">
                  {budgets.map(({ label, range }) => (
                    <label key={label} className="cursor-pointer">
                      <input 
                        type="radio" 
                        name="budget" 
                        className="peer sr-only" 
                        checked={selectedBudget === label}
                        onChange={() => setSelectedBudget(label)}
                      />
                      <div className="text-center py-2 px-1 border border-white/10 rounded-lg peer-checked:bg-primary/20 peer-checked:border-primary peer-checked:text-primary transition-all">
                        <div className="text-body-sm font-bold">{label}</div>
                        <div className="text-[10px] opacity-70 mt-0.5">{range}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2">Cuisine</label>
                <div className="flex flex-wrap gap-2">
                  {(showAllCuisines ? cuisines : cuisines.slice(0, 8)).map(cuisine => {
                    const isSelected = selectedCuisines.includes(cuisine);
                    return (
                      <span 
                        key={cuisine}
                        onClick={() => toggleCuisine(cuisine)}
                        className={`px-3 py-1.5 rounded-full border text-body-sm cursor-pointer transition-all capitalize ${
                          isSelected 
                            ? 'border-primary bg-primary/10 text-primary ai-glow-primary' 
                            : 'border-white/10 bg-surface text-on-surface hover:border-white/30'
                        }`}
                      >
                        {cuisine}
                      </span>
                    );
                  })}
                  {cuisines.length > 8 && (
                    <span
                      onClick={() => setShowAllCuisines(prev => !prev)}
                      className="px-3 py-1.5 rounded-full border border-dashed border-primary/50 text-primary/70 text-body-sm cursor-pointer hover:border-primary hover:text-primary transition-all"
                    >
                      {showAllCuisines ? "Show Less ↑" : `+${cuisines.length - 8} More`}
                    </span>
                  )}
                </div>
              </div>

              <div>
                <label className="flex justify-between font-label-caps text-label-caps text-on-surface-variant mb-2">
                  <span>Minimum Rating</span>
                  <span className="text-white font-bold">{minRating.toFixed(1)}+</span>
                </label>
                <input 
                  type="range" 
                  min="1" max="5" step="0.5" 
                  value={minRating}
                  onChange={(e) => setMinRating(parseFloat(e.target.value))}
                  className="w-full h-1 bg-surface-container rounded-lg appearance-none cursor-pointer accent-zomato-red" 
                />
              </div>

              <div>
                <label className="block font-label-caps text-label-caps text-on-surface-variant mb-2">Additional Context (AI)</label>
                <textarea 
                  className="w-full bg-surface text-white border border-white/10 rounded-lg p-3 focus:ring-1 focus:ring-zomato-red focus:border-zomato-red font-body-sm text-body-sm resize-none" 
                  placeholder="e.g., Quiet place for a romantic dinner..." 
                  rows={3}
                  value={additionalContext}
                  onChange={(e) => setAdditionalContext(e.target.value)}
                ></textarea>
              </div>

              <button 
                type="button" 
                onClick={handleRecommend}
                disabled={isLoading}
                className="w-full bg-zomato-red text-white font-title-md text-title-md py-3 rounded-lg flex items-center justify-center gap-2 ai-glow-primary hover:ai-glow-hover transition-all duration-300 hover:scale-[1.02] disabled:opacity-50"
              >
                <span className="material-symbols-outlined">auto_awesome</span>
                {isLoading ? "Analyzing..." : "Get AI Recommendations"}
              </button>
            </form>
          </div>
        </aside>

        {/* Right Content Area */}
        <section className="w-full md:w-9/12 lg:w-[70%] flex-col flex gap-6">
          <header className="flex justify-between items-end pb-2 border-b border-white/5">
            <div>
              <h1 className="font-display-lg text-display-lg text-white mb-1">AI Top Picks</h1>
              <p className="font-body-lg text-body-lg text-on-surface-variant">Curated for your taste profile</p>
            </div>
            <div className="hidden sm:flex items-center gap-2 text-on-surface-variant">
              <span className="material-symbols-outlined text-sm">sort</span>
              <span className="font-label-caps text-label-caps">Relevance</span>
            </div>
          </header>

          {error && (
            <div className="bg-red-900/50 border border-red-500 text-white p-4 rounded-lg">
              {error}
            </div>
          )}

          {isLoading && (
            <div className="flex flex-col gap-6" id="loadingState">
              {[1, 2, 3].map(i => (
                <div key={i} className="glass-panel rounded-xl h-48 flex p-4 gap-4">
                  <div className="w-40 h-full rounded-lg shimmer"></div>
                  <div className="flex-1 flex flex-col justify-between py-2">
                    <div>
                      <div className="w-3/4 h-6 shimmer rounded mb-2"></div>
                      <div className="w-1/2 h-4 shimmer rounded mb-4"></div>
                    </div>
                    <div className="w-full h-12 shimmer rounded-lg"></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {!isLoading && recommendations && (
            <div className="flex flex-col gap-6">
              <div className="bg-surface border border-white/10 rounded-lg p-4 mb-2">
                <p className="text-on-surface font-body-lg text-body-lg italic">
                  {recommendations.summary}
                </p>
              </div>

              {recommendations.recommendations.map((rec: any, idx: number) => (
                <article key={idx} className="glass-panel rounded-xl overflow-hidden group hover:-translate-y-1 transition-transform duration-300">
                  <div className="flex flex-col sm:flex-row">
                    {/* Rank Badge Column */}
                    <div className={`flex-shrink-0 w-full sm:w-20 flex items-center justify-center p-4 ${idx === 0 ? 'bg-gradient-to-b from-yellow-600/20 to-yellow-500/10' : 'bg-surface-container/50'}`}>
                      <div className="flex flex-col items-center gap-1">
                        {idx === 0 && <span className="material-symbols-outlined text-yellow-400">emoji_events</span>}
                        <span className={`font-display-lg text-display-lg font-bold ${idx === 0 ? 'text-yellow-400' : 'text-on-surface-variant'}`}>#{rec.rank || idx + 1}</span>
                      </div>
                    </div>
                    <div className="p-5 flex-1 flex flex-col justify-between">
                      <div>
                        <div className="flex justify-between items-start mb-1">
                          <h3 className="font-title-md text-title-md text-white group-hover:text-primary transition-colors">{rec.restaurant_name}</h3>
                          <div className="flex items-center bg-green-800 text-white px-2 py-0.5 rounded text-sm font-bold">
                            {rec.rating} <span className="material-symbols-outlined text-[14px] ml-1" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                          </div>
                        </div>
                        <p className="text-on-surface-variant font-body-sm text-body-sm mb-3">₹{rec.cost_for_two} for two</p>
                        <div className="flex flex-wrap gap-2 mb-4">
                          <span className="px-2 py-1 bg-surface-container rounded border border-white/5 text-xs text-on-surface-variant">{rec.cuisine}</span>
                        </div>
                      </div>
                      <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 flex gap-3 items-start relative overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-50"></div>
                        <span className="material-symbols-outlined text-primary relative z-10">lightbulb</span>
                        <p className="text-on-surface-variant font-body-sm text-body-sm italic relative z-10 text-sm">
                          "{rec.explanation}"
                        </p>
                      </div>
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}

          {!isLoading && !recommendations && !error && (
            <div className="flex flex-col items-center justify-center py-20 text-on-surface-variant">
              <span className="material-symbols-outlined text-6xl mb-4 opacity-50">restaurant_menu</span>
              <p className="font-body-lg text-body-lg">Adjust your preferences and hit "Get AI Recommendations" to see top picks!</p>
            </div>
          )}
        </section>
      </main>
    </>
  );
}
