import { useState, useEffect, useRef } from 'react';
import './WestCamera.css';

/**
 * WestCamera component - Displays live camera feed with YOLO detections
 * 
 * Polls /api/west/camera/frame every 250ms to show real-time annotated video
 * from WEST road camera. Shows camera status badge and detection count.
 */
function WestCamera() {
  const [cameraStatus, setCameraStatus] = useState({
    camera_ok: false,
    last_frame_ts: 0,
    detections: [],
    using_fake_fallback: true,
  });
  const [frameUrl, setFrameUrl] = useState('');
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;

    // Poll camera frame every 250ms
    const pollFrame = async () => {
      if (!mountedRef.current) return;

      try {
        const response = await fetch('http://localhost:8000/api/west/camera/frame');
        
        if (response.ok) {
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          
          if (mountedRef.current) {
            // Revoke old URL to prevent memory leaks
            if (frameUrl) {
              URL.revokeObjectURL(frameUrl);
            }
            setFrameUrl(url);
            setError(null);
          }
        } else {
          // Camera unavailable (503) or other error
          if (mountedRef.current) {
            setError('Camera offline or disabled');
          }
        }
      } catch (err) {
        if (mountedRef.current) {
          setError('Failed to fetch camera frame');
          console.error('Camera frame fetch error:', err);
        }
      }
    };

    // Poll camera status every 1 second (less frequent than frames)
    const pollStatus = async () => {
      if (!mountedRef.current) return;

      try {
        const response = await fetch('http://localhost:8000/api/west/camera/status');
        if (response.ok) {
          const data = await response.json();
          if (mountedRef.current) {
            setCameraStatus(data);
          }
        }
      } catch (err) {
        console.error('Camera status fetch error:', err);
      }
    };

    // Initial fetch
    pollFrame();
    pollStatus();

    // Start polling intervals
    intervalRef.current = setInterval(pollFrame, 250);
    const statusInterval = setInterval(pollStatus, 1000);

    // Cleanup on unmount
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      clearInterval(statusInterval);
      if (frameUrl) {
        URL.revokeObjectURL(frameUrl);
      }
    };
  }, []);

  const getBadgeClass = () => {
    if (cameraStatus.camera_ok && !cameraStatus.using_fake_fallback) {
      return 'camera-badge live';
    }
    return 'camera-badge offline';
  };

  const getBadgeText = () => {
    if (cameraStatus.camera_ok && !cameraStatus.using_fake_fallback) {
      return 'LIVE';
    }
    return 'OFFLINE';
  };

  const getDetectionSummary = () => {
    if (!cameraStatus.detections || cameraStatus.detections.length === 0) {
      return 'No vehicles detected';
    }

    const counts = {};
    cameraStatus.detections.forEach(det => {
      counts[det.cls_mapped] = (counts[det.cls_mapped] || 0) + 1;
    });

    return Object.entries(counts)
      .map(([type, count]) => `${count} ${type}${count > 1 ? 's' : ''}`)
      .join(', ');
  };

  return (
    <div className="west-camera">
      <div className="camera-header">
        <h3>West Road Camera</h3>
        <span className={getBadgeClass()}>{getBadgeText()}</span>
      </div>

      <div className="camera-feed">
        {error ? (
          <div className="camera-error">
            <span>📷</span>
            <p>{error}</p>
            <small>Check backend logs or enable USE_CAMERA_WEST in .env</small>
          </div>
        ) : frameUrl ? (
          <img 
            src={frameUrl} 
            alt="West road camera feed" 
            className="camera-image"
          />
        ) : (
          <div className="camera-loading">
            <span>⏳</span>
            <p>Loading camera feed...</p>
          </div>
        )}
      </div>

      <div className="camera-info">
        <div className="info-row">
          <span className="info-label">Detections:</span>
          <span className="info-value">{cameraStatus.detections?.length || 0}</span>
        </div>
        <div className="info-row detection-summary">
          <span className="info-label">Summary:</span>
          <span className="info-value">{getDetectionSummary()}</span>
        </div>
        <div className="info-row">
          <span className="info-label">Source:</span>
          <span className="info-value">
            {cameraStatus.using_fake_fallback ? 'Fake Data (Fallback)' : 'Real Camera'}
          </span>
        </div>
      </div>
    </div>
  );
}

export default WestCamera;
