from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.portal.controllers.portal import pager as portal_pager


class GameSessionCustomerPortal(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "game_sessions_count" in counters:
            values["game_sessions_count"] = (
                request.env["clinic.game.session"].search_count(
                    self._prepare_game_session_domain()
                )
                if request.env["clinic.game.session"].check_access_rights(
                    "read", raise_exception=False
                )
                else 0
            )
        return values

    def _prepare_game_session_domain(self):
        user = request.env.user
        if user.partner_type == "patient" and user.self_managed:
            return [("patient_id", "=", user.partner_id.id)]
        else:
            patients = request.env["res.users.link"].search([("user_id", "=", user.id)])
            return [("patient_id", "in", patients.mapped("patient_id.id"))]

    def _prepare_searchbar_sortings(self):
        return {
            "date": {"label": _("Newest"), "order": "session_date desc"},
        }

    @http.route(
        ["/my/game_sessions", "/my/game_sessions/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_game_sessions(
        self, page=1, date_begin=None, date_end=None, sortby=None, **kw
    ):
        values = self._prepare_portal_layout_values()
        GameSession = request.env["clinic.game.session"]
        domain = self._prepare_game_session_domain()

        searchbar_sortings = self._prepare_searchbar_sortings()
        if not sortby:
            sortby = "date"
        order = searchbar_sortings[sortby]["order"]

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        game_sessions_count = GameSession.search_count(domain)

        pager = portal_pager(
            url="/my/game_sessions",
            url_args={"date_begin": date_begin, "date_end": date_end, "sortby": sortby},
            total=game_sessions_count,
            page=page,
            step=self._items_per_page,
        )

        game_sessions = GameSession.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )

        grouped_game_sessions = {}
        for session in game_sessions:
            patient_name = session.patient_id.name or "Unknown Patient"
            if patient_name not in grouped_game_sessions:
                grouped_game_sessions[patient_name] = []
            grouped_game_sessions[patient_name].append(session)

        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "grouped_game_sessions": grouped_game_sessions,
                "page_name": "game_sessions",
                "default_url": "/my/game_sessions",
                "pager": pager,
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
            }
        )
        return request.render("clinic_management.portal_my_game_sessions", values)

    @http.route(
        ["/my/game_sessions/<int:session_id>"], type="http", auth="user", website=True
    )
    def portal_game_session_page(
        self, session_id, access_token=None, message=False, **kw
    ):
        try:
            session_sudo = self._document_check_access(
                "clinic.game.session", session_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        patient = session_sudo.patient_id
        kinesiologists = patient.patient_link_ids.filtered(
            lambda x: x.user_id.partner_id.partner_type == "kinesiologist"
        )
        guardians = patient.patient_link_ids.filtered(
            lambda x: x.user_id.partner_id.partner_type == "guardian"
        )

        domain_recent = [
            ("patient_id", "=", patient.id),
            ("id", "!=", session_id),
        ]

        recent_sessions_processed = request.env["clinic.game.session"].search(
            domain_recent + [("state", "=", "processed")],
            limit=5,
            order="session_date desc",
        )

        # If we have less than 5 processed sessions, fill with other states
        recent_sessions = recent_sessions_processed
        if len(recent_sessions_processed) < 5:
            remaining_needed = 5 - len(recent_sessions_processed)
            other_sessions = request.env["clinic.game.session"].search(
                domain_recent
                + [
                    ("state", "!=", "processed"),
                    ("id", "not in", recent_sessions_processed.ids),
                ],
                limit=remaining_needed,
                order="session_date desc",
            )
            recent_sessions = recent_sessions_processed + other_sessions

        all_sessions_including_current = (
            request.env["clinic.game.session"]
            .sudo()
            .search([("patient_id", "=", patient.id)])
        )

        total_sessions = len(all_sessions_including_current)

        processed_sessions = request.env["clinic.game.session"].search_count(
            [("patient_id", "=", patient.id), ("state", "=", "processed")]
        )

        values = {
            "game_session": session_sudo,
            "patient": patient,
            "kinesiologists": kinesiologists,
            "guardians": guardians,
            "recent_sessions": recent_sessions,
            "total_sessions": total_sessions,
            "processed_sessions": processed_sessions,
            "has_video": bool(session_sudo.video),
            "has_annotated_video": bool(
                session_sudo.video_annotated
                and session_sudo.annotated_video_state == "done"
            ),
            "has_charts": bool(
                session_sudo.state == "processed"
                and session_sudo.joint_angle_chart_combined
            ),
        }

        history_session_key = "my_game_sessions_history"
        values = self._get_page_view_values(
            session_sudo, access_token, values, history_session_key, False
        )

        return request.render("clinic_management.game_session_portal_template", values)
