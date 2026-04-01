"""Registry of all monitored system components."""

from typing import Dict, List, Optional
from .models import SystemComponent, SystemLayer

# Define all components
COMPONENTS: Dict[str, SystemComponent] = {
    # Infrastructure
    "postgres_primary": SystemComponent(
        component_id="postgres_primary",
        name="PostgreSQL Primary",
        layer=SystemLayer.INFRASTRUCTURE,
        description="Main PostgreSQL database",
        health_endpoint="postgresql://health",
        check_interval_seconds=60
    ),
    "redis_cache": SystemComponent(
        component_id="redis_cache",
        name="Redis Cache",
        layer=SystemLayer.INFRASTRUCTURE,
        description="Caching layer",
        check_interval_seconds=60
    ),
    
    # API Services
    "fastapi_main": SystemComponent(
        component_id="fastapi_main",
        name="FastAPI Main",
        layer=SystemLayer.API_SERVICES,
        description="Main FastAPI backend",
        health_endpoint="/health",
        metrics_endpoint="/metrics",
        check_interval_seconds=30
    ),
    "pipeline_coordinator": SystemComponent(
        component_id="pipeline_coordinator",
        name="Pipeline Coordinator",
        layer=SystemLayer.API_SERVICES,
        description="Job coordination service",
        health_endpoint="http://localhost:8080/health",
        check_interval_seconds=30
    ),
    
    # Data Pipeline
    "cs_extractor": SystemComponent(
        component_id="cs_extractor",
        name="CS Extractor",
        layer=SystemLayer.DATA_PIPELINE,
        description="Counter-Strike data extraction",
        check_interval_seconds=300
    ),
    "valorant_extractor": SystemComponent(
        component_id="valorant_extractor",
        name="Valorant Extractor",
        layer=SystemLayer.DATA_PIPELINE,
        description="Valorant data extraction",
        check_interval_seconds=300
    ),
    "lol_extractor": SystemComponent(
        component_id="lol_extractor",
        name="LoL Extractor",
        layer=SystemLayer.DATA_PIPELINE,
        description="League of Legends data extraction",
        check_interval_seconds=300
    ),
    
    # Web Platform
    "static_website": SystemComponent(
        component_id="static_website",
        name="Static Website (GitHub Pages)",
        layer=SystemLayer.WEB_PLATFORM,
        description="Marketing site",
        health_endpoint="https://satorx.github.io",
        check_interval_seconds=300
    ),
    "react_web_app": SystemComponent(
        component_id="react_web_app",
        name="SATOR Web (Vercel)",
        layer=SystemLayer.WEB_PLATFORM,
        description="React web application",
        health_endpoint="https://sator-web.vercel.app",
        check_interval_seconds=60
    ),
    
    # External
    "supabase": SystemComponent(
        component_id="supabase",
        name="Supabase",
        layer=SystemLayer.EXTERNAL,
        description="PostgreSQL hosting",
        health_endpoint="https://status.supabase.com",
        check_interval_seconds=300
    ),
    "render_api": SystemComponent(
        component_id="render_api",
        name="Render (API)",
        layer=SystemLayer.EXTERNAL,
        description="API hosting",
        health_endpoint="https://status.render.com",
        check_interval_seconds=300
    ),
    "vercel": SystemComponent(
        component_id="vercel",
        name="Vercel",
        layer=SystemLayer.EXTERNAL,
        description="Frontend hosting",
        health_endpoint="https://www.vercel-status.com",
        check_interval_seconds=300
    ),
}


class ComponentRegistry:
    """Registry for managing system components."""
    
    def __init__(self, components: Optional[Dict[str, SystemComponent]] = None):
        self._components = (components or COMPONENTS).copy()
    
    def get(self, component_id: str) -> SystemComponent:
        """Get a component by ID.
        
        Args:
            component_id: The unique component identifier
            
        Returns:
            The SystemComponent instance
            
        Raises:
            KeyError: If component not found
        """
        return self._components[component_id]
    
    def get_optional(self, component_id: str) -> Optional[SystemComponent]:
        """Get a component by ID, returning None if not found.
        
        Args:
            component_id: The unique component identifier
            
        Returns:
            The SystemComponent instance or None
        """
        return self._components.get(component_id)
    
    def get_by_layer(self, layer: SystemLayer) -> List[SystemComponent]:
        """Get all components in a specific layer.
        
        Args:
            layer: The system layer to filter by
            
        Returns:
            List of components in the layer
        """
        return [c for c in self._components.values() if c.layer == layer]
    
    def get_by_layers(self, layers: List[SystemLayer]) -> List[SystemComponent]:
        """Get all components in multiple layers.
        
        Args:
            layers: List of system layers to filter by
            
        Returns:
            List of components in the specified layers
        """
        return [c for c in self._components.values() if c.layer in layers]
    
    def get_all(self) -> List[SystemComponent]:
        """Get all registered components.
        
        Returns:
            List of all components
        """
        return list(self._components.values())
    
    def get_all_ids(self) -> List[str]:
        """Get all registered component IDs.
        
        Returns:
            List of component IDs
        """
        return list(self._components.keys())
    
    def register(self, component: SystemComponent) -> None:
        """Register a new component.
        
        Args:
            component: The component to register
        """
        self._components[component.component_id] = component
    
    def unregister(self, component_id: str) -> bool:
        """Remove a component from the registry.
        
        Args:
            component_id: The component ID to remove
            
        Returns:
            True if removed, False if not found
        """
        if component_id in self._components:
            del self._components[component_id]
            return True
        return False
    
    def update(self, component: SystemComponent) -> bool:
        """Update an existing component.
        
        Args:
            component: The component with updated values
            
        Returns:
            True if updated, False if not found
        """
        if component.component_id in self._components:
            self._components[component.component_id] = component
            return True
        return False
    
    def filter(self, **kwargs) -> List[SystemComponent]:
        """Filter components by attributes.
        
        Args:
            **kwargs: Attribute name-value pairs to filter by
            
        Returns:
            List of matching components
        """
        results = []
        for component in self._components.values():
            match = True
            for key, value in kwargs.items():
                if not hasattr(component, key) or getattr(component, key) != value:
                    match = False
                    break
            if match:
                results.append(component)
        return results
    
    def get_dependencies(self, component_id: str) -> List[SystemComponent]:
        """Get all components that a component depends on.
        
        Args:
            component_id: The component to get dependencies for
            
        Returns:
            List of dependency components
        """
        component = self._components.get(component_id)
        if not component:
            return []
        
        return [
            self._components[dep_id] 
            for dep_id in component.depends_on 
            if dep_id in self._components
        ]
    
    def get_dependents(self, component_id: str) -> List[SystemComponent]:
        """Get all components that depend on a given component.
        
        Args:
            component_id: The component to get dependents for
            
        Returns:
            List of dependent components
        """
        return [
            component 
            for component in self._components.values()
            if component_id in component.depends_on
        ]
    
    def get_layer_summary(self) -> Dict[SystemLayer, int]:
        """Get count of components per layer.
        
        Returns:
            Dictionary mapping layers to component counts
        """
        summary = {layer: 0 for layer in SystemLayer}
        for component in self._components.values():
            summary[component.layer] = summary.get(component.layer, 0) + 1
        return summary
    
    def __len__(self) -> int:
        """Return the number of registered components."""
        return len(self._components)
    
    def __contains__(self, component_id: str) -> bool:
        """Check if a component ID is registered."""
        return component_id in self._components
    
    def __iter__(self):
        """Iterate over registered components."""
        return iter(self._components.values())


# Default registry instance
default_registry = ComponentRegistry()
