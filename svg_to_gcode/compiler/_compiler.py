import typing
import warnings

from svg_to_gcode.compiler.interfaces import Interface
from svg_to_gcode.geometry import Curve, Line
from svg_to_gcode.geometry import LineSegmentChain
from svg_to_gcode import UNITS, TOLERANCES


class Compiler:
    def __init__(self, interface_class: typing.Type[Interface], movement_speed, cutting_speed, pass_depth,
                 dwell_time=0, unit=None, custom_header=None, custom_footer=None):

        self.interface = interface_class()
        self.movement_speed = movement_speed
        self.cutting_speed = cutting_speed
        self.pass_depth = abs(pass_depth)
        self.dwell_time = dwell_time

        if (unit is not None) and (unit not in UNITS):
            raise ValueError(f"Unknown unit {unit}. Please specify one of the following: {UNITS}")
        
        self.unit = unit

        # 🔄 Substituindo laser_off pelo Z5 (caneta levantada)
        if custom_header is None:
            custom_header = ["G1 Z5 ; caneta levantada"]

        if custom_footer is None:
            custom_footer = ["G1 Z5 ; caneta levantada"]

        self.header = [
            "G90 ; coordenadas absolutas",
            f"G1 F{self.movement_speed}"
        ] + custom_header

        self.footer = custom_footer
        self.body = []

    def compile(self, passes=1):
        if len(self.body) == 0:
            warnings.warn("Compile with an empty body (no curves). Is this intentional?")

        gcode = []

        gcode.extend(self.header)

        if self.unit:
            gcode.append(f"G21 ; unidade: {self.unit}")

        for i in range(passes):
            gcode.extend(self.body)

            if i < passes - 1:
                gcode.append("G1 Z5 ; caneta levantada")
                if self.pass_depth > 0:
                    gcode.append("G91 ; coordenadas relativas")
                    gcode.append(f"G1 Z{-self.pass_depth:.3f} ; descendo para próxima passada")
                    gcode.append("G90 ; coordenadas absolutas")

        gcode.extend(self.footer)

        gcode = filter(lambda command: len(command) > 0, gcode)

        return '\n'.join(gcode)

    def compile_to_file(self, file_name: str, passes=1):
        with open(file_name, 'w') as file:
            file.write(self.compile(passes=passes))

    def append_line_chain(self, line_chain: LineSegmentChain):
        if line_chain.chain_size() == 0:
            warnings.warn("Attempted to parse empty LineChain")
            return []

        code = []

        start = line_chain.get(0).start

        # Se o ponto de início for novo, levanta caneta, move rápido, abaixa e desenha
        if self.interface.position is None or abs(self.interface.position - start) > TOLERANCES["operation"]:
            code = [
                "G1 Z5 ; caneta levantada",
                f"G1 F{self.movement_speed}",
                f"G1 X{start.x:.3f} Y{start.y:.3f}",
                f"G1 F{self.cutting_speed}",
                "G1 Z0 ; caneta abaixa"
            ]

            if self.dwell_time > 0:
                code.insert(0, f"G4 P{int(self.dwell_time)}")

        for line in line_chain:
            code.append(f"G1 X{line.end.x:.3f} Y{line.end.y:.3f}")

        self.body.extend(code)

    def append_curves(self, curves: [typing.Type[Curve]]):
        for curve in curves:
            line_chain = LineSegmentChain()
            approximation = LineSegmentChain.line_segment_approximation(curve)
            line_chain.extend(approximation)
            self.append_line_chain(line_chain)
