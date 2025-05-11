'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { aiService } from '@/lib/api';
import { useAuth } from '@/lib/hooks/useAuth';

type TimeRange = 'day' | 'week' | 'month' | 'year';

export default function AnalyticsPage() {
  const { user } = useAuth();
  const [timeRange, setTimeRange] = useState<TimeRange>('week');
  const [usageMetrics, setUsageMetrics] = useState<any>(null);
  const [costData, setCostData] = useState<any>(null);
  const [responseTimeData, setResponseTimeData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    // Check if user is admin
    if (user) {
      setIsAdmin(user.role === 'admin');
    }
  }, [user]);

  useEffect(() => {
    const fetchAnalyticsData = async () => {
      try {
        setIsLoading(true);
        
        // In a real implementation, these would be actual API calls
        // const usageResponse = await aiService.getAIUsageMetrics(timeRange);
        // const costResponse = await aiService.getCostOptimizationData(timeRange);
        // const responseTimeResponse = await aiService.getResponseTimeMetrics(timeRange);
        
        // Mock data for now
        setTimeout(() => {
          // Mock usage metrics
          setUsageMetrics({
            total_requests: 1250,
            total_tokens: 3450000,
            average_tokens_per_request: 2760,
            unique_users: 85,
            most_active_hours: [14, 15, 16], // 2-4 PM
            request_distribution: {
              tutoring: 65,
              quiz_generation: 20,
              content_summarization: 15
            }
          });
          
          // Mock cost data
          setCostData({
            total_cost: 127.50,
            cost_by_feature: {
              tutoring: 82.88,
              quiz_generation: 25.50,
              content_summarization: 19.12
            },
            cost_trend: [
              { date: '2025-05-03', cost: 15.20 },
              { date: '2025-05-04', cost: 18.75 },
              { date: '2025-05-05', cost: 21.30 },
              { date: '2025-05-06', cost: 19.85 },
              { date: '2025-05-07', cost: 17.60 },
              { date: '2025-05-08', cost: 16.90 },
              { date: '2025-05-09', cost: 17.90 }
            ],
            optimization_recommendations: [
              'Implement caching for common tutoring queries',
              'Reduce token usage in quiz generation prompts',
              'Optimize context window size for content summarization'
            ]
          });
          
          // Mock response time data
          setResponseTimeData({
            average_response_time: 2.3, // seconds
            p95_response_time: 4.1, // seconds
            response_time_distribution: [
              { range: '0-1s', percentage: 15 },
              { range: '1-2s', percentage: 35 },
              { range: '2-3s', percentage: 30 },
              { range: '3-4s', percentage: 12 },
              { range: '4-5s', percentage: 5 },
              { range: '5s+', percentage: 3 }
            ]
          });
          
          setIsLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Error fetching analytics data:', error);
        setIsLoading(false);
      }
    };

    if (isAdmin) {
      fetchAnalyticsData();
    } else {
      setIsLoading(false);
    }
  }, [timeRange, isAdmin]);

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <h1 className="text-2xl font-bold mb-4">Access Restricted</h1>
        <p className="text-gray-600 mb-6">You need administrator privileges to view this page.</p>
        <Button onClick={() => window.history.back()}>Go Back</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold tracking-tight">AI Analytics Dashboard</h1>
        <div className="flex space-x-2">
          <Button 
            variant={timeRange === 'day' ? 'primary' : 'outline'}
            onClick={() => setTimeRange('day')}
          >
            Day
          </Button>
          <Button 
            variant={timeRange === 'week' ? 'primary' : 'outline'}
            onClick={() => setTimeRange('week')}
          >
            Week
          </Button>
          <Button 
            variant={timeRange === 'month' ? 'primary' : 'outline'}
            onClick={() => setTimeRange('month')}
          >
            Month
          </Button>
          <Button 
            variant={timeRange === 'year' ? 'primary' : 'outline'}
            onClick={() => setTimeRange('year')}
          >
            Year
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Usage Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{usageMetrics?.total_requests.toLocaleString()}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{usageMetrics?.total_tokens.toLocaleString()}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Avg. Tokens/Request</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{usageMetrics?.average_tokens_per_request.toLocaleString()}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Unique Users</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{usageMetrics?.unique_users}</div>
              </CardContent>
            </Card>
          </div>

          {/* Cost Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Cost Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium">Total Cost:</span>
                  <span className="text-xl font-bold">${costData?.total_cost.toFixed(2)}</span>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Cost by Feature:</h4>
                  <div className="space-y-2">
                    {costData?.cost_by_feature && Object.entries(costData.cost_by_feature).map(([feature, cost]: [string, any]) => (
                      <div key={feature} className="flex justify-between">
                        <span className="capitalize">{feature.replace('_', ' ')}:</span>
                        <span>${cost.toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Cost Trend:</h4>
                  <div className="h-40 flex items-end space-x-2">
                    {costData?.cost_trend.map((item: any, index: number) => {
                      const height = (item.cost / Math.max(...costData.cost_trend.map((i: any) => i.cost))) * 100;
                      return (
                        <div key={index} className="flex flex-col items-center flex-1">
                          <div 
                            className="w-full bg-primary-600 rounded-t" 
                            style={{ height: `${height}%` }}
                          ></div>
                          <div className="text-xs mt-1 truncate w-full text-center">
                            {new Date(item.date).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Response Time Analysis */}
          <Card>
            <CardHeader>
              <CardTitle>Response Time Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="mb-4">
                    <div className="text-sm font-medium mb-1">Average Response Time</div>
                    <div className="text-2xl font-bold">{responseTimeData?.average_response_time.toFixed(1)}s</div>
                  </div>
                  
                  <div>
                    <div className="text-sm font-medium mb-1">95th Percentile Response Time</div>
                    <div className="text-2xl font-bold">{responseTimeData?.p95_response_time.toFixed(1)}s</div>
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium mb-2">Response Time Distribution</h4>
                  <div className="space-y-2">
                    {responseTimeData?.response_time_distribution.map((item: any, index: number) => (
                      <div key={index} className="space-y-1">
                        <div className="flex justify-between text-xs">
                          <span>{item.range}</span>
                          <span>{item.percentage}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-1.5">
                          <div 
                            className="bg-primary-600 h-1.5 rounded-full" 
                            style={{ width: `${item.percentage}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Optimization Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle>Cost Optimization Recommendations</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {costData?.optimization_recommendations.map((recommendation: string, index: number) => (
                  <li key={index} className="flex items-start">
                    <span className="mr-2 text-primary-600">u2022</span>
                    <span>{recommendation}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
