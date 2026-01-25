from typing import List
from core.models import BoundVisual, VisualLayout

class LayoutPlanner:
    """
    Decides the position and size of visuals on the canvas.
    """
    CANVAS_WIDTH = 1280
    CANVAS_HEIGHT = 720
    PADDING = 20
    
    # Standard grid (e.g., 2 columns, 3 rows) - customizable
    GRID_COLS = 2
    GRID_ROWS = 2

    def plan_layout(self, visuals: List[BoundVisual], dashboard_title: str = "Dashboard") -> List[BoundVisual]:
        """
        Assigns x, y, width, height, tabOrder to each visual.
        """
        # TODO: integrate LLM here to assign "Zones" (Header, Sidebar, Main)
        # For now, use a smart flow algorithm to place them in a grid.
        
        updated_visuals = []
        
        # 0. HEADER (Compulsory)
        header_height = 40 # Approx from template (37.85)
        header_y = 10      # Approx from template (10.59)
        header_x = 13      # Approx from template (13.62)
        header_width = self.CANVAS_WIDTH - 2 * header_x # Center it roughly
        
        header_visual = BoundVisual(
            visual_name="dashboard_header",
            visual_type="textbox",
            title=dashboard_title, # This will be the text content
            bindings=[],
            layout=VisualLayout(
                x=int(header_x),
                y=int(header_y),
                width=int(1246), # From template
                height=int(header_height),
                tabOrder=0
            )
        )
        updated_visuals.append(header_visual)

        # Simple Logic:
        # 1. Cards take top row (small height)
        # 2. Others take remaining grid
        
        cards = [v for v in visuals if v.visual_type == "card"]
        charts = [v for v in visuals if v.visual_type != "card"]
        
        # Start Y below header
        current_y = header_y + header_height + self.PADDING
        
        # PLACE CARDS (Top Row)
        # PLACE CARDS (Stacked Vertically)
        if cards:
            card_height = 110
            card_width = 1240
            card_x = (self.CANVAS_WIDTH - card_width) // 2 # Center it: (1280 - 1240) / 2 = 20
            
            for i, card in enumerate(cards):
                layout = VisualLayout(
                    x=int(card_x),
                    y=int(current_y),
                    width=int(card_width),
                    height=int(card_height),
                    tabOrder=i + 1
                )
                card.layout = layout
                updated_visuals.append(card)
                
                # Increment Y for next card (stacking)
                current_y += card_height + self.PADDING
            
        # PLACE CHARTS (Grid below)
        if charts:
            # Dynamic grid based on count
            count = len(charts)
            cols = 2 if count > 1 else 1
            rows = (count + cols - 1) // cols
            
            avail_width = self.CANVAS_WIDTH - 2 * self.PADDING
            avail_height = self.CANVAS_HEIGHT - current_y - self.PADDING
            
            chart_width = (avail_width - (cols - 1) * self.PADDING) / cols
            chart_height = (avail_height - (rows - 1) * self.PADDING) / rows
            
            base_tab_order = len(cards) + 1
            
            for i, chart in enumerate(charts):
                row = i // cols
                col = i % cols
                
                layout = VisualLayout(
                    x=int(self.PADDING + col * (chart_width + self.PADDING)),
                    y=int(current_y + row * (chart_height + self.PADDING)),
                    width=int(chart_width),
                    height=int(chart_height),
                    tabOrder=base_tab_order + i
                )
                chart.layout = layout
                updated_visuals.append(chart)
                
        # Re-merge to preserve original order if needed, but returning processed list is fine
        return updated_visuals

