import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, CheckCircle, AlertTriangle, Eye, RefreshCw } from 'lucide-react';

interface WorkingSetServer {
  name: string;
  required: boolean;
  description: string;
}

interface WorkingSet {
  name: string;
  id: string;
  description: string;
  icon: string;
  category: string;
  servers: WorkingSetServer[];
  server_count: number;
  is_current: boolean;
}

interface PreviewData {
  current_servers: string[];
  new_servers: string[];
  added_servers: string[];
  removed_servers: string[];
  config_preview: any;
}

export function WorkingSetSwitcher() {
  const [workingSets, setWorkingSets] = useState<WorkingSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState<string | null>(null);
  const [preview, setPreview] = useState<PreviewData | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkingSets();
  }, []);

  const loadWorkingSets = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/working-sets/');
      if (!response.ok) throw new Error('Failed to load working sets');
      const data = await response.json();
      setWorkingSets(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load working sets');
    } finally {
      setLoading(false);
    }
  };

  const switchWorkingSet = async (workingSetId: string) => {
    try {
      setSwitching(workingSetId);
      const response = await fetch(`/api/working-sets/${workingSetId}/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ working_set_id: workingSetId, create_backup: true })
      });
      
      if (!response.ok) throw new Error('Failed to switch working set');
      
      // Reload working sets to update current status
      await loadWorkingSets();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to switch working set');
    } finally {
      setSwitching(null);
    }
  };

  const previewWorkingSet = async (workingSetId: string) => {
    try {
      setPreviewLoading(true);
      const response = await fetch(`/api/working-sets/${workingSetId}/preview`);
      if (!response.ok) throw new Error('Failed to load preview');
      const data = await response.json();
      setPreview(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load preview');
    } finally {
      setPreviewLoading(false);
    }
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      'Development': 'bg-blue-100 text-blue-800',
      'Creative': 'bg-purple-100 text-purple-800',
      'Productivity': 'bg-green-100 text-green-800',
      'Automation': 'bg-orange-100 text-orange-800',
      'Entertainment': 'bg-pink-100 text-pink-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-6 w-6 animate-spin mr-2" />
        Loading working sets...
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Working Sets</h1>
          <p className="text-gray-600 mt-1">
            Switch between focused MCP server configurations for different workflows
          </p>
        </div>
        <Button
          onClick={loadWorkingSets}
          variant="outline"
          size="sm"
          className="flex items-center gap-2"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {workingSets.map((workingSet) => (
          <Card 
            key={workingSet.id}
            className={`transition-all duration-200 hover:shadow-lg ${
              workingSet.is_current 
                ? 'ring-2 ring-green-500 bg-green-50' 
                : 'hover:shadow-md'
            }`}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-2xl">{workingSet.icon}</span>
                  <div>
                    <CardTitle className="text-lg">{workingSet.name}</CardTitle>
                    <Badge 
                      variant="secondary" 
                      className={`text-xs mt-1 ${getCategoryColor(workingSet.category)}`}
                    >
                      {workingSet.category}
                    </Badge>
                  </div>
                </div>
                {workingSet.is_current && (
                  <CheckCircle className="h-5 w-5 text-green-600" />
                )}
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <CardDescription className="text-sm">
                {workingSet.description}
              </CardDescription>

              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">
                  {workingSet.server_count} MCP servers
                </span>
                <Badge variant="outline" className="text-xs">
                  {workingSet.servers.filter(s => s.required).length} required
                </Badge>
              </div>

              <div className="flex flex-wrap gap-1 max-h-16 overflow-hidden">
                {workingSet.servers.slice(0, 6).map((server) => (
                  <Badge 
                    key={server.name}
                    variant={server.required ? "default" : "secondary"}
                    className="text-xs"
                  >
                    {server.name}
                  </Badge>
                ))}
                {workingSet.servers.length > 6 && (
                  <Badge variant="outline" className="text-xs">
                    +{workingSet.servers.length - 6} more
                  </Badge>
                )}
              </div>

              <div className="flex gap-2 pt-2">
                <Button
                  onClick={() => switchWorkingSet(workingSet.id)}
                  disabled={workingSet.is_current || switching === workingSet.id}
                  className="flex-1"
                  variant={workingSet.is_current ? "secondary" : "default"}
                >
                  {switching === workingSet.id ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Switching...
                    </>
                  ) : workingSet.is_current ? (
                    'Active'
                  ) : (
                    'Activate'
                  )}
                </Button>

                <Dialog>
                  <DialogTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => previewWorkingSet(workingSet.id)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle className="flex items-center gap-2">
                        <span className="text-xl">{workingSet.icon}</span>
                        Preview: {workingSet.name}
                      </DialogTitle>
                      <DialogDescription>
                        Preview the configuration changes for this working set
                      </DialogDescription>
                    </DialogHeader>

                    {previewLoading ? (
                      <div className="flex items-center justify-center p-8">
                        <Loader2 className="h-6 w-6 animate-spin mr-2" />
                        Loading preview...
                      </div>
                    ) : preview ? (
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <h4 className="font-medium text-green-700 mb-2">
                              ✅ Added Servers ({preview.added_servers.length})
                            </h4>
                            <div className="space-y-1">
                              {preview.added_servers.map(server => (
                                <Badge key={server} variant="default" className="mr-1">
                                  {server}
                                </Badge>
                              ))}
                              {preview.added_servers.length === 0 && (
                                <p className="text-sm text-gray-500">No servers added</p>
                              )}
                            </div>
                          </div>

                          <div>
                            <h4 className="font-medium text-red-700 mb-2">
                              ❌ Removed Servers ({preview.removed_servers.length})
                            </h4>
                            <div className="space-y-1">
                              {preview.removed_servers.map(server => (
                                <Badge key={server} variant="destructive" className="mr-1">
                                  {server}
                                </Badge>
                              ))}
                              {preview.removed_servers.length === 0 && (
                                <p className="text-sm text-gray-500">No servers removed</p>
                              )}
                            </div>
                          </div>
                        </div>

                        <div>
                          <h4 className="font-medium mb-2">
                            📋 All Servers in Working Set ({preview.new_servers.length})
                          </h4>
                          <div className="flex flex-wrap gap-1">
                            {preview.new_servers.map(server => (
                              <Badge key={server} variant="secondary">
                                {server}
                              </Badge>
                            ))}
                          </div>
                        </div>

                        <div className="pt-4">
                          <Button
                            onClick={() => switchWorkingSet(workingSet.id)}
                            disabled={workingSet.is_current}
                            className="w-full"
                          >
                            {workingSet.is_current ? 'Already Active' : 'Switch to This Working Set'}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <p>Click to load preview</p>
                    )}
                  </DialogContent>
                </Dialog>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {workingSets.length === 0 && !loading && (
        <div className="text-center py-12">
          <p className="text-gray-500">No working sets found</p>
          <Button onClick={loadWorkingSets} className="mt-4">
            Retry Loading
          </Button>
        </div>
      )}
    </div>
  );
}