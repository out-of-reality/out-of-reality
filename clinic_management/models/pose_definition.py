import json
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PoseDefinition(models.Model):
    _name = "pose.definition"
    _description = "Definición de Poses Personalizadas"
    _rec_name = "name"
    _order = "name"

    name = fields.Char(string="Nombre de la Pose", required=True, index=True, copy=True)
    description = fields.Text(string="Descripción", copy=True)
    active = fields.Boolean(string="Activo", default=True, index=True)

    angle_requirements_ids = fields.One2many(
        "pose.angle.requirement", "pose_id", string="Requisitos de Ángulos", copy=True
    )

    require_feet_on_ground = fields.Boolean(
        string="Requiere Pies en el Suelo",
        default=True,
        copy=True,
        help="Si está marcado, la pose solo se detectará si los pies están en el suelo",
    )
    foot_tolerance_y = fields.Float(
        string="Tolerancia Y para Pies",
        default=0.08,
        copy=True,
        help="Tolerancia para verificar si "
        'los puntos del pie están "cercanos" en Y (pie plano)',
    )

    @api.constrains("angle_requirements_ids")
    def _check_angle_requirements(self):
        for record in self:
            if not record.angle_requirements_ids:
                raise ValidationError(
                    _("Una pose debe tener al menos un requisito de ángulo definido.")
                )

    @api.constrains("foot_tolerance_y")
    def _check_foot_tolerance(self):
        for record in self:
            if not (0 <= record.foot_tolerance_y <= 1):
                raise ValidationError(
                    _("La tolerancia para pies debe estar entre 0 y 1.")
                )

    @api.constrains("require_feet_on_ground", "foot_tolerance_y")
    def _check_foot_tolerance_range(self):
        """Validación automática de tolerancia de pies con advertencia"""
        for record in self:
            if record.require_feet_on_ground and not (
                0.01 <= record.foot_tolerance_y <= 0.5
            ):
                # Mostrar warning pero no bloquear
                return {
                    "warning": {
                        "title": _("Advertencia de Configuración"),
                        "message": _(
                            "Tolerancia de pies (%.3f) "
                            "fuera del rango recomendado (0.01-0.5)."
                        )
                        % record.foot_tolerance_y,
                    }
                }

    def get_pose_data_for_unity(self):
        """Retorna los datos de la pose en formato JSON para Unity"""
        self.ensure_one()
        angle_requirements = [
            {
                "angle": req.angle_type,
                "min_angle": req.min_angle,
                "max_angle": req.max_angle,
                "description": req.description or "",
            }
            for req in self.angle_requirements_ids
        ]

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "angle_requirements": angle_requirements,
            "require_feet_on_ground": self.require_feet_on_ground,
            "foot_tolerance_y": self.foot_tolerance_y,
            "active": self.active,
        }

    @api.model
    def export_all_poses_for_unity(self, *args, **kwargs):
        """Exporta todas las poses activas para Unity"""
        active_poses = self.search([("active", "=", True)], order="name")
        poses_data = [pose.get_pose_data_for_unity() for pose in active_poses]

        export = {
            "poses": poses_data,
            "total_poses": len(poses_data),
            "timestamp": fields.Datetime.now().isoformat(),
        }

        _logger.info(
            "Exportación completa de poses:\n%s",
            json.dumps(export, indent=2, ensure_ascii=False),
        )
        return export
