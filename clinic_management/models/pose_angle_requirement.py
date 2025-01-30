import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..utils.video_processor import JointAngles

_logger = logging.getLogger(__name__)


class PoseAngleRequirement(models.Model):
    _name = "pose.angle.requirement"
    _description = "Requisito de Ángulo para Pose"
    _order = "angle_type"

    pose_id = fields.Many2one(
        "pose.definition", string="Pose", required=True, ondelete="cascade", index=True
    )
    angle_type = fields.Selection(
        selection="_get_angle_type_selection", string="Tipo de Ángulo", required=True
    )
    min_angle = fields.Float(
        string="Ángulo Mínimo (°)",
        required=True,
        digits=(5, 2),
        help="Ángulo mínimo en grados para considerar válido este requisito",
    )
    max_angle = fields.Float(
        string="Ángulo Máximo (°)",
        required=True,
        digits=(5, 2),
        help="Ángulo máximo en grados para considerar válido este requisito",
    )
    description = fields.Text(string="Descripción del Requisito")

    angle_range = fields.Float(
        string="Rango Angular (°)",
        compute="_compute_angle_metrics",
        store=True,
        digits=(5, 2),
        help="Diferencia entre el ángulo máximo y mínimo",
    )
    angle_midpoint = fields.Float(
        string="Punto Medio (°)",
        compute="_compute_angle_metrics",
        store=True,
        digits=(5, 2),
        help="Punto medio del rango angular",
    )

    @api.model
    def _get_angle_type_selection(self):
        try:
            return [
                (angle.name, angle.name.replace("_", " ").title())
                for angle in JointAngles
            ]
        except Exception as e:
            _logger.error(f"Error al generar la selección de tipos de ángulo: {e}")
            return []

    @api.depends("min_angle", "max_angle")
    def _compute_angle_metrics(self):
        for record in self:
            if record.max_angle is not None and record.min_angle is not None:
                record.angle_range = record.max_angle - record.min_angle
                record.angle_midpoint = (record.min_angle + record.max_angle) / 2
            else:
                record.angle_range = 0
                record.angle_midpoint = 0

    def _validate_unique_angle_per_pose(self):
        """Validación interna para ángulos únicos por pose"""
        for record in self:
            if not record.pose_id or not record.angle_type:
                continue

            # Buscar duplicados excluyendo el registro actual
            domain = [
                ("pose_id", "=", record.pose_id.id),
                ("angle_type", "=", record.angle_type),
                ("id", "!=", record.id),
            ]

            existing = self.search(domain, limit=1)
            if existing:
                # Obtener el label del ángulo
                angle_label = record.angle_type
                try:
                    selection_dict = dict(self._get_angle_type_selection())
                    angle_label = selection_dict.get(
                        record.angle_type, record.angle_type
                    )
                except Exception as e:
                    _logger.warning("Error getting angle label for validation: %s", e)

                raise ValidationError(
                    _(
                        "El ángulo '%(angle_type)s' ya está definido "
                        "para la pose '%(pose_name)s'."
                    )
                    % {"angle_type": angle_label, "pose_name": record.pose_id.name}
                )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create para validar al crear"""
        records = super().create(vals_list)
        records._validate_unique_angle_per_pose()
        return records

    def write(self, vals):
        """Override write para validar al modificar"""
        result = super().write(vals)

        # Solo validar si se cambió pose_id o angle_type
        if "pose_id" in vals or "angle_type" in vals:
            self._validate_unique_angle_per_pose()

        return result

    @api.constrains("min_angle", "max_angle")
    def _check_angles(self):
        """Validación de rangos de ángulos"""
        for record in self:
            # Validaciones críticas que bloquean el guardado
            if record.min_angle is not None and record.min_angle < 0:
                raise ValidationError(
                    _(
                        "Ángulo %(angle_type)s: "
                        "el mínimo (%(min_angle)s°) no puede ser negativo."
                    )
                    % {"angle_type": record.angle_type, "min_angle": record.min_angle}
                )

            if record.max_angle is not None and record.max_angle > 180:
                raise ValidationError(
                    _("Ángulo %(angle_type)s: el máximo (%(max_angle)s°) excede 180°.")
                    % {"angle_type": record.angle_type, "max_angle": record.max_angle}
                )

            if (
                record.min_angle is not None
                and record.max_angle is not None
                and record.min_angle >= record.max_angle
            ):
                raise ValidationError(
                    _(
                        "Ángulo %(angle_type)s: el mínimo (%(min_angle)s°) "
                        "debe ser menor que el máximo (%(max_angle)s°)."
                    )
                    % {
                        "angle_type": record.angle_type,
                        "min_angle": record.min_angle,
                        "max_angle": record.max_angle,
                    }
                )

    @api.onchange("min_angle", "max_angle")
    def _onchange_validate_angles(self):
        """Validación en tiempo real con advertencias"""
        if not self.min_angle or not self.max_angle:
            return

        warnings = []

        # Validaciones básicas
        if self.min_angle < 0:
            warnings.append("⚠️ El ángulo mínimo no puede ser negativo.")

        if self.max_angle > 180:
            warnings.append("⚠️ El ángulo máximo excede 180°.")

        if self.min_angle >= self.max_angle:
            warnings.append("⚠️ El ángulo mínimo debe ser menor que el máximo.")

        # Advertencias de rango
        if self.min_angle < self.max_angle:
            angle_range = self.max_angle - self.min_angle
            if angle_range > 90:
                warnings.append(
                    "⚠️ Rango muy amplio (%.1f°), puede ser poco específico."
                    % angle_range
                )
            elif angle_range < 10:
                warnings.append(
                    "⚠️ Rango muy estrecho (%.1f°), puede ser difícil de detectar."
                    % angle_range
                )

        if warnings:
            return {
                "warning": {
                    "title": _("Advertencia de Configuración"),
                    "message": "\n".join(warnings),
                }
            }

    @api.onchange("angle_type", "pose_id")
    def _onchange_check_duplicate_angle(self):
        """Verificación en tiempo real de ángulos duplicados"""
        if not self.pose_id or not self.angle_type:
            return

        # Para registros nuevos (sin ID) o existentes
        domain = [
            ("pose_id", "=", self.pose_id.id),
            ("angle_type", "=", self.angle_type),
        ]

        # Si es un registro existente, excluirlo de la búsqueda
        if self.id:
            domain.append(("id", "!=", self.id))

        existing = self.search(domain, limit=1)
        if existing:
            # Obtener el label del ángulo
            angle_label = self.angle_type
            try:
                selection_dict = dict(self._get_angle_type_selection())
                angle_label = selection_dict.get(self.angle_type, self.angle_type)
            except Exception as e:
                _logger.warning("Error getting angle label for duplicate check: %s", e)

            return {
                "warning": {
                    "title": _("Ángulo Duplicado"),
                    "message": _(
                        "El ángulo '%(angle_type)s' ya está definido para esta pose."
                    )
                    % {"angle_type": angle_label},
                }
            }
