"""
Patent Claims to Mermaid Diagram Generator
=========================================

A production-level system that converts patent claims into USPTO-compliant 
Mermaid diagrams for patent drawings. This demonstrates legal-AI integration
and automated document generation for patent prosecution.

Author: [Your Name]
Created for: Thomson Reuters Innovation Team Application
"""

import re
import json
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComponentType(Enum):
    """Standard patent drawing component types with appropriate Mermaid symbols"""
    PROCESS = "rectangle"      # Standard processing unit
    DATABASE = "cylinder"      # Data storage, memory
    DECISION = "diamond"       # Logic branching, conditions  
    INTERFACE = "parallelogram" # Input/output, user interface
    STORAGE = "cylinder"       # Storage systems
    CONTROLLER = "rectangle"   # Control systems
    SENSOR = "parallelogram"   # Input devices
    DISPLAY = "parallelogram"  # Output devices
    NETWORK = "circle"         # Network nodes
    DOCUMENT = "document"      # Files, records

@dataclass
class PatentComponent:
    """Represents a component extracted from patent claims"""
    name: str
    reference_num: int
    component_type: ComponentType
    description: str = ""
    relationships: List[str] = field(default_factory=list)
    
    def to_mermaid_node(self) -> str:
        """Convert component to Mermaid node syntax"""
        node_id = f"COMP{self.reference_num}"
        display_name = f"{self.name} {self.reference_num}"
        
        if self.component_type == ComponentType.DATABASE or self.component_type == ComponentType.STORAGE:
            return f'{node_id}[("{display_name}")]'
        elif self.component_type == ComponentType.DECISION:
            return f'{node_id}{{{display_name}}}'
        elif self.component_type == ComponentType.INTERFACE or self.component_type == ComponentType.SENSOR:
            return f'{node_id}[/{display_name}/]'
        elif self.component_type == ComponentType.DISPLAY:
            return f'{node_id}[/"{display_name}"/]'
        elif self.component_type == ComponentType.NETWORK:
            return f'{node_id}(({display_name}))'
        elif self.component_type == ComponentType.DOCUMENT:
            return f'{node_id}[["{display_name}"]]'
        else:  # Default rectangle for processes, controllers
            return f'{node_id}[{display_name}]'

@dataclass
class PatentConnection:
    """Represents a connection between components"""
    from_component: str
    to_component: str
    label: str
    connection_type: str = "data_flow"
    
    def to_mermaid_connection(self) -> str:
        """Convert to Mermaid connection syntax with USPTO styling"""
        styled_label = f'<span style="font-size:24px;font-weight:bold;background:white;padding:6px">{self.label}</span>'
        return f'{self.from_component} -.->|"{styled_label}"| {self.to_component}'

class PatentClaimsParser:
    """Parses patent claims to extract components and relationships"""
    
    def __init__(self):
        self.component_patterns = {
            ComponentType.PROCESS: [
                r'processing unit', r'processor', r'processing system',
                r'computing device', r'processing module'
            ],
            ComponentType.DATABASE: [
                r'database', r'data store', r'storage system', r'memory',
                r'data repository', r'storage device'
            ],
            ComponentType.CONTROLLER: [
                r'controller', r'control unit', r'control system',
                r'control module', r'control device'
            ],
            ComponentType.INTERFACE: [
                r'interface', r'user interface', r'communication interface',
                r'network interface', r'input interface'
            ],
            ComponentType.SENSOR: [
                r'sensor', r'detector', r'monitoring device',
                r'measurement device', r'input device'
            ],
            ComponentType.DISPLAY: [
                r'display', r'screen', r'monitor', r'output device',
                r'visual display', r'user display'
            ]
        }
        
        self.relationship_patterns = [
            r'connected to', r'coupled to', r'in communication with',
            r'operatively connected', r'electrically connected',
            r'configured to receive', r'configured to send',
            r'transmits to', r'receives from'
        ]
    
    def parse_claims(self, claims_text: str) -> Tuple[List[PatentComponent], List[PatentConnection]]:
        """Parse patent claims to extract components and relationships"""
        logger.info("Starting patent claims parsing")
        
        components = self._extract_components(claims_text)
        connections = self._extract_relationships(claims_text, components)
        
        logger.info(f"Extracted {len(components)} components and {len(connections)} connections")
        return components, connections
    
    def _extract_components(self, text: str) -> List[PatentComponent]:
        """Extract components from claims text"""
        components = []
        reference_counter = 10  # Patent convention: start with 10, increment by 2
        
        # Look for component mentions with reference numbers
        component_pattern = r'([a-zA-Z\s]+?)\s*\((\d+)\)'
        matches = re.findall(component_pattern, text)
        
        for match in matches:
            component_name = match[0].strip()
            ref_num = int(match[1])
            component_type = self._classify_component(component_name)
            
            component = PatentComponent(
                name=component_name,
                reference_num=ref_num,
                component_type=component_type
            )
            components.append(component)
        
        # If no reference numbers found, extract components and assign numbers
        if not components:
            for comp_type, patterns in self.component_patterns.items():
                for pattern in patterns:
                    matches = re.findall(rf'\b{pattern}\b', text, re.IGNORECASE)
                    for match in matches:
                        if not any(comp.name.lower() == match.lower() for comp in components):
                            component = PatentComponent(
                                name=match.title(),
                                reference_num=reference_counter,
                                component_type=comp_type
                            )
                            components.append(component)
                            reference_counter += 2
        
        return components
    
    def _classify_component(self, component_name: str) -> ComponentType:
        """Classify component based on name patterns"""
        name_lower = component_name.lower()
        
        for comp_type, patterns in self.component_patterns.items():
            if any(pattern in name_lower for pattern in patterns):
                return comp_type
        
        return ComponentType.PROCESS  # Default
    
    def _extract_relationships(self, text: str, components: List[PatentComponent]) -> List[PatentConnection]:
        """Extract relationships between components"""
        connections = []
        
        # Simple relationship extraction based on proximity and keywords
        for i, comp1 in enumerate(components):
            for j, comp2 in enumerate(components[i+1:], i+1):
                # Look for relationship indicators between components
                for pattern in self.relationship_patterns:
                    if re.search(rf'{comp1.name}.*?{pattern}.*?{comp2.name}', text, re.IGNORECASE):
                        connection = PatentConnection(
                            from_component=f"COMP{comp1.reference_num}",
                            to_component=f"COMP{comp2.reference_num}",
                            label=pattern.title()
                        )
                        connections.append(connection)
                        break
        
        return connections

class MermaidGenerator:
    """Generates USPTO-compliant Mermaid diagrams from patent components"""
    
    def __init__(self):
        self.mermaid_config = '''%%{init: {
  'theme':'base', 
  'themeVariables': { 
    'primaryColor': '#ffffff', 
    'primaryTextColor': '#000000', 
    'primaryBorderColor': '#000000', 
    'lineColor': '#000000', 
    'background': '#ffffff', 
    'mainBkg': '#ffffff', 
    'secondBkg': '#ffffff', 
    'tertiaryBkg': '#ffffff', 
    'edgeLabelBackground': '#ffffff',
    'clusterBkg': 'rgba(0,0,0,0)',
    'altBackground': '#ffffff',
    'cScale0': '#ffffff', 
    'cScale1': '#ffffff', 
    'cScale2': '#ffffff'
  }, 
  'flowchart': {'curve': 'linear'}, 
  'fontSize': 20
}}%%'''
    
    def generate_diagram(self, components: List[PatentComponent], 
                        connections: List[PatentConnection],
                        title: str = "PATENT SYSTEM DIAGRAM") -> str:
        """Generate complete USPTO-compliant Mermaid diagram"""
        
        logger.info("Generating Mermaid diagram")
        
        lines = [self.mermaid_config, "", "flowchart TB"]
        
        # Add title
        lines.extend([
            f'    TITLE["{title}"]',
            ""
        ])
        
        # Group components by type for better organization
        grouped_components = self._group_components_by_type(components)
        
        # Generate subgraphs for different component types
        for comp_type, comps in grouped_components.items():
            if len(comps) > 1:
                lines.extend(self._generate_subgraph(comp_type, comps))
            else:
                # Single components outside subgraphs
                for comp in comps:
                    lines.append(f"    {comp.to_mermaid_node()}")
        
        lines.append("")
        
        # Add connections
        for conn in connections:
            lines.append(f"    {conn.to_mermaid_connection()}")
        
        lines.extend(["", self._generate_styling(components)])
        
        return "\n".join(lines)
    
    def _group_components_by_type(self, components: List[PatentComponent]) -> Dict[ComponentType, List[PatentComponent]]:
        """Group components by their type for organized subgraphs"""
        grouped = {}
        for comp in components:
            if comp.component_type not in grouped:
                grouped[comp.component_type] = []
            grouped[comp.component_type].append(comp)
        return grouped
    
    def _generate_subgraph(self, comp_type: ComponentType, components: List[PatentComponent]) -> List[str]:
        """Generate subgraph for component group"""
        subgraph_name = f"{comp_type.name}_SYS"
        subgraph_title = f"{comp_type.name.replace('_', ' ')} SYSTEM"
        
        lines = [
            f'    subgraph {subgraph_name} [" "]',
            f'        direction TB',
            f'        {subgraph_name}_TITLE["{subgraph_title}"]'
        ]
        
        # Add components
        for comp in components:
            lines.append(f"        {comp.to_mermaid_node()}")
        
        # Add title connection
        if components:
            lines.append(f"        {subgraph_name}_TITLE ~~~ COMP{components[0].reference_num}")
        
        lines.append("    end")
        lines.append("")
        
        return lines
    
    def _generate_styling(self, components: List[PatentComponent]) -> str:
        """Generate styling for USPTO compliance"""
        styling_lines = [
            "    %% USPTO-Compliant Styling",
            "    classDef default fill:#ffffff,stroke:#000000,stroke-width:3px,color:#000000,font-size:20px,font-weight:bold"
        ]
        
        # Add component class assignments
        comp_ids = [f"COMP{comp.reference_num}" for comp in components]
        if comp_ids:
            styling_lines.append(f"    class {','.join(comp_ids)} default")
        
        return "\n".join(styling_lines)

class PatentDrawingGenerator:
    """Main application class for generating patent drawings from claims"""
    
    def __init__(self):
        self.parser = PatentClaimsParser()
        self.generator = MermaidGenerator()
    
    def process_claims_file(self, input_file: Path, output_file: Path) -> None:
        """Process patent claims file and generate Mermaid diagram"""
        logger.info(f"Processing claims file: {input_file}")
        
        try:
            # Read claims text
            with open(input_file, 'r', encoding='utf-8') as f:
                claims_text = f.read()
            
            # Parse claims
            components, connections = self.parser.parse_claims(claims_text)
            
            if not components:
                logger.warning("No components found in claims text")
                return
            
            # Generate diagram
            diagram_title = f"PATENT SYSTEM - {input_file.stem.upper()}"
            mermaid_code = self.generator.generate_diagram(components, connections, diagram_title)
            
            # Write output
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(mermaid_code)
            
            logger.info(f"Generated Mermaid diagram: {output_file}")
            
            # Generate metadata file
            metadata = {
                "input_file": str(input_file),
                "components_found": len(components),
                "connections_found": len(connections),
                "components": [
                    {
                        "name": comp.name,
                        "reference_num": comp.reference_num,
                        "type": comp.component_type.name
                    } for comp in components
                ]
            }
            
            metadata_file = output_file.with_suffix('.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Generated metadata: {metadata_file}")
            
        except Exception as e:
            logger.error(f"Error processing file {input_file}: {str(e)}")
            raise
    
    def batch_process(self, input_dir: Path, output_dir: Path) -> None:
        """Process multiple claims files in batch"""
        logger.info(f"Batch processing: {input_dir} -> {output_dir}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for input_file in input_dir.glob("*.txt"):
            output_file = output_dir / f"{input_file.stem}_diagram.mmd"
            self.process_claims_file(input_file, output_file)

def main():
    """Command line interface for the patent drawing generator"""
    parser = argparse.ArgumentParser(
        description="Generate USPTO-compliant patent drawings from claims text"
    )
    parser.add_argument("input", type=Path, help="Input claims file or directory")
    parser.add_argument("-o", "--output", type=Path, help="Output file or directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    generator = PatentDrawingGenerator()
    
    if args.input.is_file():
        # Single file processing
        output_file = args.output or args.input.with_suffix('.mmd')
        generator.process_claims_file(args.input, output_file)
    elif args.input.is_dir():
        # Batch processing
        output_dir = args.output or (args.input / "diagrams")
        generator.batch_process(args.input, output_dir)
    else:
        logger.error(f"Input path does not exist: {args.input}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
