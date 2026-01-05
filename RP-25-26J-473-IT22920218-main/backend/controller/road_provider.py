# backend/controller/road_provider.py
"""
Road count providers: unified interface for getting traffic counts from various sources.

Supports:
- FakeProvider: generates synthetic traffic (for N/E/S)
- HybridProvider: combines fake (N/E/S) + YOLO camera (WEST)
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class RoadProviderBase(ABC):
    """Abstract base for road count providers."""
    
    @abstractmethod
    def get_counts(self) -> Dict[str, Dict[str, int]]:
        """
        Get vehicle counts for all roads.
        
        Returns:
            {
                "north": {"car": N, "bike": N, ...},
                "east": {...},
                "south": {...},
                "west": {...}
            }
        """
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict:
        """
        Get metadata about data sources.
        
        Returns:
            {
                "west_source": "camera|fake",
                "camera_ok": bool,
                "last_frame_ts": float,
                ...
            }
        """
        pass


class FakeProvider(RoadProviderBase):
    """
    Generates synthetic traffic for all roads.
    Wraps yolo_fake_generator without changes.
    """
    
    def __init__(self, fake_generator):
        """
        Args:
            fake_generator: YoloFakeGenerator instance
        """
        self.fake_gen = fake_generator
        logger.info("FakeProvider initialized (all roads use synthetic data)")
    
    def get_counts(self) -> Dict[str, Dict[str, int]]:
        """Get fake counts for all roads."""
        counts_obj = self.fake_gen.next_counts()
        return {
            "north": counts_obj.north.dict(),
            "east": counts_obj.east.dict(),
            "south": counts_obj.south.dict(),
            "west": counts_obj.west.dict(),
        }
    
    def get_metadata(self) -> Dict:
        """Return fake provider metadata."""
        return {
            "west_source": "fake",
            "camera_ok": False,
            "last_frame_ts": 0.0,
        }


class HybridProvider(RoadProviderBase):
    """
    Hybrid provider: uses YOLO camera for WEST, fake generator for N/E/S.
    
    Single source of truth for controller decision logic.
    """
    
    def __init__(self, fake_provider: FakeProvider, yolo_west_source=None):
        """
        Args:
            fake_provider: FakeProvider instance for N/E/S
            yolo_west_source: YoloWestSource instance (optional, if None uses fake for WEST too)
        """
        self.fake_provider = fake_provider
        self.yolo_west = yolo_west_source
        self.last_log_time = 0.0
        
        if yolo_west_source:
            logger.info("HybridProvider initialized: N/E/S=fake, WEST=YOLO camera")
        else:
            logger.info("HybridProvider initialized: all roads=fake (camera disabled)")
    
    def get_counts(self) -> Dict[str, Dict[str, int]]:
        """
        Get counts: WEST from camera (if ok), else fake. N/E/S always fake.
        """
        # Get N/E/S from fake
        fake_counts = self.fake_provider.get_counts()
        
        # Get WEST from camera or fall back to fake
        west_counts = fake_counts["west"].copy()  # default fallback
        used_camera = False
        
        if self.yolo_west:
            try:
                camera_west = self.yolo_west.get_latest_counts()
                # Check if camera_west has any actual data (not all zeros and not empty)
                if camera_west and isinstance(camera_west, dict) and sum(camera_west.values()) > 0:
                    west_counts = camera_west.copy()
                    used_camera = True
                    logger.info(f"[PROVIDER] Using CAMERA WEST counts: {camera_west}")
            except Exception as e:
                logger.error(f"[PROVIDER] Failed to get WEST from camera: {e}", exc_info=True)
        
        return {
            "north": fake_counts["north"],
            "east": fake_counts["east"],
            "south": fake_counts["south"],
            "west": west_counts,
        }
    
    def get_metadata(self) -> Dict:
        """Get metadata including data sources."""
        west_source = "fake"
        camera_ok = False
        last_frame_ts = 0.0
        
        if self.yolo_west:
            try:
                status = self.yolo_west.get_status()
                camera_ok = status.get("camera_ok", False)
                last_frame_ts = status.get("last_frame_ts", 0.0)
                west_source = "camera" if camera_ok else "fake"
            except Exception as e:
                logger.warning(f"Failed to get camera status: {e}")
        
        return {
            "west_source": west_source,
            "camera_ok": camera_ok,
            "last_frame_ts": last_frame_ts,
        }
    
    def tick(self):
        """Optional: call this to advance internal state if needed."""
        pass
