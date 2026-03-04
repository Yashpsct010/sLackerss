"use client";

import React, { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart,
} from "recharts";
import {
  AlertCircle,
  TrendingUp,
  Package,
  CheckCircle,
  PackageSearch,
} from "lucide-react";

export default function Dashboard() {
  const [forecastData, setForecastData] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSku, setSelectedSku] = useState("HOBBIES_1_001");
  const [restockingId, setRestockingId] = useState<string | null>(null);

  const fetchData = async (sku: string) => {
    try {
      setLoading(true);
      const location = "LOC-1";

      const fRes = await fetch(
        `http://localhost:8000/api/v1/forecasts/${sku}?horizon=DAILY`,
      );
      if (fRes.ok) {
        const fData = await fRes.json();
        const chartData = fData.predictions.map(
          (p: {
            date: string;
            point_forecast: number;
            lower_bound: number;
            upper_bound: number;
          }) => ({
            date: p.date,
            forecast: p.point_forecast,
            range: [p.lower_bound, p.upper_bound],
          }),
        );
        setForecastData(chartData);
      }

      const rRes = await fetch(
        `http://localhost:8000/api/v1/recommendations/${location}`,
      );
      if (rRes.ok) {
        const rData = await rRes.json();
        setRecommendations(rData.recommendations);
      }
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(selectedSku);
  }, [selectedSku]);

  const handleRestock = async (sku: string, quantity: number) => {
    try {
      setRestockingId(sku);
      const res = await fetch(
        `http://localhost:8000/api/v1/recommendations/${sku}/restock`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ quantity }),
        },
      );

      if (res.ok) {
        alert(`Successfully ordered ${quantity} units of ${sku}`);
        // Refresh data to show updated inventory
        await fetchData(selectedSku);
      }
    } catch (error) {
      console.error("Error restocking:", error);
      alert("Failed to place order.");
    } finally {
      setRestockingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6 font-sans">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Demand Intelligence Copilot
          </h1>
          <p className="text-slate-500 mt-1">
            AI-powered forecasts & inventory optimization
          </p>
        </div>
        <div className="flex items-center gap-3 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
          <div className="h-2 w-2 rounded-full bg-emerald-500"></div>
          <span className="text-sm font-medium text-slate-600">
            Ensemble Model Active (XGBoost + ARIMA)
          </span>
        </div>
      </header>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Chart Area */}
          <div className="col-span-1 lg:col-span-2 space-y-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h2 className="text-xl font-semibold text-slate-800">
                    Forecast vs Confidence Interval
                  </h2>
                  <p className="text-sm text-slate-500">
                    SKU: {selectedSku} | Next 30 Days
                  </p>
                </div>
                <select
                  value={selectedSku}
                  onChange={(e) => setSelectedSku(e.target.value)}
                  className="bg-blue-50 border border-blue-200 text-blue-700 font-medium rounded-md px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer hover:bg-blue-100 transition-colors"
                >
                  <option value="HOBBIES_1_001">HOBBIES_1_001 (Hobbies)</option>
                  <option value="HOUSEHOLD_1_001">
                    HOUSEHOLD_1_001 (Household)
                  </option>
                  <option value="FOODS_1_001">FOODS_1_001 (Grocery)</option>
                </select>
              </div>

              <div className="h-[400px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart
                    data={forecastData}
                    margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                  >
                    <CartesianGrid
                      strokeDasharray="3 3"
                      vertical={false}
                      stroke="#e2e8f0"
                    />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 12, fill: "#64748b" }}
                      tickFormatter={(val) =>
                        new Date(val).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })
                      }
                    />
                    <YAxis tick={{ fontSize: 12, fill: "#64748b" }} />
                    <Tooltip
                      content={({ active, payload, label }) => {
                        if (active && payload && payload.length) {
                          // Date string
                          const dateStr = new Date(label).toLocaleDateString(
                            "en-US",
                            {
                              weekday: "short",
                              year: "numeric",
                              month: "short",
                              day: "numeric",
                            },
                          );

                          // Find corresponding data points
                          const ciPayload = payload.find(
                            (p: { name: string; value: number[] }) =>
                              p.name === "95% Confidence Interval",
                          );
                          const forecastPayload = payload.find(
                            (p: { name: string; value: number }) =>
                              p.name === "Predicted Demand",
                          );

                          return (
                            <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-md min-w-[220px]">
                              {/* Top Level: Primary Predicted Demand (Strongest Color & Weight) */}
                              {forecastPayload && (
                                <div className="mb-2 pb-2 border-b border-slate-100 flex justify-between items-center">
                                  <span className="text-sm font-extrabold text-blue-700">
                                    Predicted Demand
                                  </span>
                                  <span className="text-sm font-black text-slate-900">
                                    {forecastPayload.value}
                                  </span>
                                </div>
                              )}

                              <div className="space-y-1">
                                {/* Second Level: Date Context (Medium Strength) */}
                                <div className="flex justify-between items-center">
                                  <span className="text-xs font-semibold text-slate-500">
                                    Date
                                  </span>
                                  <span className="text-xs font-bold text-slate-700">
                                    {dateStr}
                                  </span>
                                </div>

                                {/* Third Level: Confidence Interval (Weakest Strength / Supportive Data) */}
                                {ciPayload &&
                                  ciPayload.value &&
                                  Array.isArray(ciPayload.value) && (
                                    <div className="flex justify-between items-center">
                                      <span className="text-xs font-medium text-slate-400">
                                        95% Interval
                                      </span>
                                      <span className="text-xs font-medium text-slate-500">
                                        {ciPayload.value[0]} ~{" "}
                                        {ciPayload.value[1]}
                                      </span>
                                    </div>
                                  )}
                              </div>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Legend />
                    <Area
                      type="monotone"
                      dataKey="range"
                      stroke="none"
                      fill="#bfdbfe"
                      fillOpacity={0.4}
                      name="95% Confidence Interval"
                    />
                    <Line
                      type="monotone"
                      dataKey="forecast"
                      stroke="#3b82f6"
                      strokeWidth={3}
                      dot={false}
                      activeDot={{ r: 6 }}
                      name="Predicted Demand"
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
                <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                  <TrendingUp className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-sm text-slate-500 font-medium">
                    Model Accuracy (MAPE)
                  </p>
                  <p className="text-2xl font-bold text-slate-800">
                    {selectedSku === "HOBBIES_1_001"
                      ? "82.0%"
                      : selectedSku === "HOUSEHOLD_1_001"
                        ? "86.0%"
                        : "93.0%"}
                  </p>
                </div>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
                <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                  <Package className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-sm text-slate-500 font-medium">
                    Auto-Optimized SKUs
                  </p>
                  <p className="text-2xl font-bold text-slate-800">1,248</p>
                </div>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-start gap-4">
                <div className="p-3 bg-rose-50 text-rose-600 rounded-lg">
                  <AlertCircle className="h-6 w-6" />
                </div>
                <div>
                  <p className="text-sm text-slate-500 font-medium">
                    Active Stock Alerts
                  </p>
                  <p className="text-2xl font-bold text-slate-800">
                    {recommendations.length}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Sidebar: Recommendations */}
          <div className="col-span-1 space-y-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm h-full max-h-[640px] overflow-y-auto">
              <h2 className="text-xl font-semibold text-slate-800 mb-6 flex items-center gap-2">
                <PackageSearch className="h-5 w-5 text-indigo-500" />
                Actionable Intelligence
              </h2>

              <div className="space-y-4">
                {recommendations.length > 0 ? (
                  recommendations.map(
                    (
                      rec: {
                        sku: string;
                        location: string;
                        priority_score: number;
                        current_inventory: number;
                        reorder_point: number;
                        recommended_order_quantity: number;
                        order_by_date: string;
                      },
                      idx: number,
                    ) => {
                      const isCritical = rec.priority_score > 80;
                      const isHigh =
                        rec.priority_score > 50 && rec.priority_score <= 80;

                      return (
                        <div
                          key={idx}
                          className={`p-4 rounded-xl border ${isCritical ? "border-rose-200 bg-rose-50/50" : isHigh ? "border-amber-200 bg-amber-50/50" : "border-slate-200 bg-slate-50"} shadow-sm relative overflow-hidden`}
                        >
                          {isCritical && (
                            <div className="absolute top-0 left-0 w-1 h-full bg-rose-500"></div>
                          )}
                          {isHigh && (
                            <div className="absolute top-0 left-0 w-1 h-full bg-amber-500"></div>
                          )}

                          <div className="flex justify-between items-start mb-3">
                            <div>
                              <p className="font-bold text-slate-800">
                                {rec.sku}
                              </p>
                              <p className="text-xs text-slate-500">
                                Loc: {rec.location}
                              </p>
                            </div>
                            <span
                              className={`text-xs font-bold px-2 py-1 rounded-full ${isCritical ? "bg-rose-100 text-rose-700" : isHigh ? "bg-amber-100 text-amber-700" : "bg-slate-100 text-slate-700"}`}
                            >
                              Score: {Math.round(rec.priority_score)}
                            </span>
                          </div>

                          <div className="grid grid-cols-2 gap-2 mb-4 text-sm">
                            <div className="bg-white p-2 rounded border border-slate-100">
                              <p className="text-slate-500 text-xs">Current</p>
                              <p className="font-semibold text-slate-800">
                                {rec.current_inventory}
                              </p>
                            </div>
                            <div className="bg-white p-2 rounded border border-slate-100">
                              <p className="text-slate-500 text-xs">
                                Reorder Pt
                              </p>
                              <p className="font-semibold text-slate-800">
                                {rec.reorder_point}
                              </p>
                            </div>
                          </div>

                          <div className="bg-white p-3 rounded-lg border border-indigo-100 mb-4">
                            <p className="text-xs font-semibold text-indigo-600 mb-1 uppercase tracking-wider">
                              AI Recommendation
                            </p>
                            <p className="text-sm font-medium text-slate-800">
                              Order {rec.recommended_order_quantity} units
                            </p>
                            <p className="text-xs text-slate-500 mt-1">
                              Order by: {rec.order_by_date}
                            </p>
                          </div>

                          <button
                            onClick={() =>
                              handleRestock(
                                rec.sku,
                                rec.recommended_order_quantity,
                              )
                            }
                            disabled={restockingId === rec.sku}
                            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-medium py-2.5 rounded-lg transition-colors shadow-sm flex justify-center items-center cursor-pointer disabled:cursor-not-allowed"
                          >
                            {restockingId === rec.sku ? (
                              <span className="animate-pulse">
                                Processing Order...
                              </span>
                            ) : (
                              "1-Click Restock"
                            )}
                          </button>
                        </div>
                      );
                    },
                  )
                ) : (
                  <p className="text-slate-500 text-sm text-center py-10 flex flex-col items-center gap-2">
                    <CheckCircle className="h-8 w-8 text-emerald-500" />
                    All inventory levels are healthy.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
