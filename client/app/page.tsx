"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, Video, Play, Square, Radio } from "lucide-react";

interface Incident {
  id: string;
  timestamp: Date;
  threat: boolean;
  description: string;
  filename?: string;
  loading?: boolean;
}

export default function Home() {
  const [isRecording, setIsRecording] = useState(false);
  const [cameraStream, setCameraStream] = useState<MediaStream | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDevice, setSelectedDevice] = useState<string>("");
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recordingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const videoCounterRef = useRef(0);

  useEffect(() => {
    // Get available video devices
    navigator.mediaDevices.enumerateDevices().then((devices) => {
      const videoDevs = devices.filter((d) => d.kind === "videoinput");
      setVideoDevices(videoDevs);
      if (videoDevs.length > 0) {
        setSelectedDevice(videoDevs[0].deviceId);
      }
    });
  }, []);

  useEffect(() => {
    if (cameraStream && videoRef.current) {
      videoRef.current.srcObject = cameraStream;
    }

    return () => {
      if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [cameraStream]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: selectedDevice ? { deviceId: selectedDevice } : true,
        audio: false,
      });
      setCameraStream(stream);
    } catch (error) {
      console.error("Error accessing camera:", error);
      alert("Failed to access camera. Please check permissions.");
    }
  };

  const stopCamera = () => {
    if (cameraStream) {
      cameraStream.getTracks().forEach((track) => track.stop());
      setCameraStream(null);
    }
    if (isRecording) {
      stopRecording();
    }
  };

  const uploadVideo = async (blob: Blob): Promise<void> => {
    const fileName = `${videoCounterRef.current}.webm`;
    videoCounterRef.current++;
    const formData = new FormData();
    formData.append("video", blob, fileName);

    // Create loading incident card
    const incidentId = `incident-${Date.now()}`;
    const loadingIncident: Incident = {
      id: incidentId,
      timestamp: new Date(),
      threat: false,
      description: "Analyzing video...",
      filename: fileName,
      loading: true,
    };
    setIncidents((prev) => [loadingIncident, ...prev]);

    try {
      const response = await fetch("http://localhost:5002/save-video", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Failed to save video: ${response.statusText}`);
      }

      const result = await response.json();
      let geminiData;
      
      if (typeof result.gemini_response === "string") {
        geminiData = JSON.parse(result.gemini_response);
      } else {
        geminiData = result.gemini_response;
      }

      // Update incident with results
      setIncidents((prev) =>
        prev.map((inc) =>
          inc.id === incidentId
            ? {
                ...inc,
                threat: geminiData.threat === 1,
                description: geminiData.description || "No description available",
                loading: false,
              }
            : inc
        )
      );
    } catch (error) {
      console.error("Error uploading video:", error);
      setIncidents((prev) =>
        prev.map((inc) =>
          inc.id === incidentId
            ? {
                ...inc,
                description: `Error: ${error instanceof Error ? error.message : "Failed to analyze video"}`,
                loading: false,
              }
            : inc
        )
      );
    }
  };

  const startRecording = () => {
    if (!cameraStream) {
      alert("Please start camera first");
      return;
    }

    setIsRecording(true);

    const recordChunk = () => {
      if (!cameraStream) return;

      const mimeTypes = [
        "video/webm;codecs=vp8",
        "video/webm;codecs=vp9",
        "video/webm",
        "video/mp4",
      ];

      let selectedMimeType = null;
      for (const type of mimeTypes) {
        if (MediaRecorder.isTypeSupported(type)) {
          selectedMimeType = type;
          break;
        }
      }

      if (!selectedMimeType) {
        console.error("No supported MIME type found");
        return;
      }

      const mediaRecorder = new MediaRecorder(cameraStream, {
        mimeType: selectedMimeType,
      });

      const chunks: Blob[] = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: selectedMimeType || "video/webm" });
        uploadVideo(blob);
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;

      setTimeout(() => {
        if (mediaRecorder.state !== "inactive") {
          mediaRecorder.stop();
        }
      }, 5000);
    };

    // Record first chunk immediately
    recordChunk();

    // Then record every 5 seconds
    recordingIntervalRef.current = setInterval(recordChunk, 5000);
  };

  const stopRecording = () => {
    setIsRecording(false);
    if (recordingIntervalRef.current) {
      clearInterval(recordingIntervalRef.current);
      recordingIntervalRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              ClampsAI
            </h1>
            <p className="text-muted-foreground mt-1">
              Real-time security monitoring with AI threat detection
            </p>
          </div>
          <div className="flex items-center gap-2">
            {isRecording && (
              <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                <Radio className="h-4 w-4 animate-pulse" />
                <span className="text-sm font-medium">LIVE</span>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Camera Feed */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Video className="h-5 w-5" />
                  Camera Feed
                </CardTitle>
                <CardDescription>
                  Select a camera and start monitoring
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {videoDevices.length > 0 && (
                  <select
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={selectedDevice}
                    onChange={(e) => setSelectedDevice(e.target.value)}
                    disabled={!!cameraStream}
                  >
                    {videoDevices.map((device) => (
                      <option key={device.deviceId} value={device.deviceId}>
                        {device.label || `Camera ${device.deviceId.slice(0, 8)}`}
                      </option>
                    ))}
                  </select>
                )}

                <div className="relative aspect-video bg-black rounded-lg overflow-hidden border-2 border-slate-200 dark:border-slate-700">
                  {cameraStream ? (
                    <video
                      ref={videoRef}
                      autoPlay
                      muted
                      playsInline
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                      <div className="text-center">
                        <Video className="h-12 w-12 mx-auto mb-2 opacity-50" />
                        <p>No camera feed</p>
                      </div>
                    </div>
                  )}
                  {isRecording && (
                    <div className="absolute top-4 right-4 bg-red-600 text-white px-3 py-1 rounded-full text-xs font-medium flex items-center gap-2">
                      <Radio className="h-3 w-3 animate-pulse" />
                      RECORDING
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  {!cameraStream ? (
                    <Button onClick={startCamera} className="flex-1">
                      <Video className="h-4 w-4 mr-2" />
                      Start Camera
                    </Button>
                  ) : (
                    <>
                      {!isRecording ? (
                        <Button onClick={startRecording} className="flex-1" variant="destructive">
                          <Play className="h-4 w-4 mr-2" />
                          Start Monitoring
                        </Button>
                      ) : (
                        <Button onClick={stopRecording} className="flex-1" variant="destructive">
                          <Square className="h-4 w-4 mr-2" />
                          Stop Monitoring
                        </Button>
                      )}
                      <Button onClick={stopCamera} variant="outline">
                        Stop Camera
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Incidents */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  Incidents
                </CardTitle>
                <CardDescription>
                  {incidents.length} total {incidents.length === 1 ? "analysis" : "analyses"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="live" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="live">Live</TabsTrigger>
                    <TabsTrigger value="all">All</TabsTrigger>
                  </TabsList>
                  <TabsContent value="live" className="mt-4">
                    <div className="space-y-3 max-h-[600px] overflow-y-auto">
                      {incidents
                        .filter((inc) => !inc.loading)
                        .map((incident) => (
                          <Card
                            key={incident.id}
                            className={
                              incident.threat
                                ? "border-red-500 bg-red-50 dark:bg-red-950/20"
                                : ""
                            }
                          >
                            <CardHeader className="pb-3">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <CardTitle className="text-sm flex items-center gap-2">
                                    {incident.threat && (
                                      <Badge variant="destructive" className="text-xs">
                                        THREAT
                                      </Badge>
                                    )}
                                    {!incident.threat && (
                                      <Badge variant="secondary" className="text-xs">
                                        CLEAR
                                      </Badge>
                                    )}
                                  </CardTitle>
                                  <CardDescription className="text-xs mt-1">
                                    {incident.timestamp.toLocaleTimeString()}
                                  </CardDescription>
                                </div>
                              </div>
                            </CardHeader>
                            <CardContent>
                              <p className="text-sm text-muted-foreground">
                                {incident.description}
                              </p>
                            </CardContent>
                          </Card>
                        ))}
                      {incidents.filter((inc) => !inc.loading).length === 0 && (
                        <div className="text-center py-8 text-muted-foreground">
                          <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                          <p className="text-sm">No incidents yet</p>
                          <p className="text-xs mt-1">
                            Start monitoring to see analysis results
                          </p>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                  <TabsContent value="all" className="mt-4">
                    <div className="space-y-3 max-h-[600px] overflow-y-auto">
                      {incidents.map((incident) => (
                        <Card
                          key={incident.id}
                          className={
                            incident.threat
                              ? "border-red-500 bg-red-50 dark:bg-red-950/20"
                              : incident.loading
                              ? "border-blue-500 bg-blue-50 dark:bg-blue-950/20"
                              : ""
                          }
                        >
                          <CardHeader className="pb-3">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <CardTitle className="text-sm flex items-center gap-2">
                                  {incident.loading ? (
                                    <Badge variant="outline" className="text-xs">
                                      ANALYZING
                                    </Badge>
                                  ) : incident.threat ? (
                                    <Badge variant="destructive" className="text-xs">
                                      THREAT
                                    </Badge>
                                  ) : (
                                    <Badge variant="secondary" className="text-xs">
                                      CLEAR
                                    </Badge>
                                  )}
                                </CardTitle>
                                <CardDescription className="text-xs mt-1">
                                  {incident.timestamp.toLocaleString()}
                                </CardDescription>
                              </div>
                            </div>
                          </CardHeader>
                          <CardContent>
                            {incident.loading ? (
                              <div className="flex items-center gap-2">
                                <div className="h-2 w-2 bg-blue-500 rounded-full animate-pulse" />
                                <p className="text-sm text-muted-foreground">
                                  Analyzing video...
                                </p>
                              </div>
                            ) : (
                              <p className="text-sm text-muted-foreground">
                                {incident.description}
                              </p>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                      {incidents.length === 0 && (
                        <div className="text-center py-8 text-muted-foreground">
                          <AlertCircle className="h-8 w-8 mx-auto mb-2 opacity-50" />
                          <p className="text-sm">No incidents yet</p>
                        </div>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
