import re
import ast
import operator
import random
import sqlite3
from discord.ext import commands
from src.database import get_db_connection

# Evaluator seguro de expressões matemáticas usando AST
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def safe_eval(node):
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError("Constante inválida")
    elif isinstance(node, ast.BinOp):
        left = safe_eval(node.left)
        right = safe_eval(node.right)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](left, right)
        raise ValueError(f"Operador não suportado: {op_type}")
    elif isinstance(node, ast.UnaryOp):
        operand = safe_eval(node.operand)
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            return SAFE_OPERATORS[op_type](operand)
        raise ValueError(f"Operador unário não suportado: {op_type}")
    else:
        raise ValueError(f"Sintaxe não suportada: {type(node)}")

def evaluate_math_string(expr_str: str) -> float:
    parsed = ast.parse(expr_str.strip(), mode='eval')
    return safe_eval(parsed)


class EnemyManager:
    """Gerenciador de Fichas de Inimigos / Criaturas RPG em Banco de Dados Local SQLite."""
    
    @classmethod
    def get_template(cls) -> str:
        return (
            "📋 **Modelo de Ficha de Inimigo:**\n"
            "```text\n"
            "!set {Enemy Sheet}Name: \"Nome do Inimigo\"; HP: 50; AC: 15;\n"
            "```\n"
            "Substitua os valores dentro das aspas ou após os dois pontos!"
        )

    @classmethod
    def create_or_update_enemy(cls, text: str, guild_id: str = "global") -> str:
        name_m = re.search(r'Name:\s*["“]?([^"”;]+)["”]?\s*;?', text, re.IGNORECASE)
        hp_m = re.search(r'HP:\s*["“]?(\d+)["”]?\s*;?', text, re.IGNORECASE)
        ac_m = re.search(r'AC:\s*["“]?(\d*)["”]?\s*;?', text, re.IGNORECASE)

        if not name_m or not hp_m:
            return cls.get_template()

        name = name_m.group(1).strip()
        max_hp = int(hp_m.group(1))
        ac = ac_m.group(1).strip() if ac_m and ac_m.group(1) else "N/A"
        key = name.lower()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO enemy_sheets (guild_id, name, name_lower, current_hp, max_hp, ac, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Alive')
            ON CONFLICT(name_lower) DO UPDATE SET
                current_hp=excluded.current_hp,
                max_hp=excluded.max_hp,
                ac=excluded.ac,
                status='Alive'
        """, (guild_id, name, key, max_hp, max_hp, ac))
        conn.commit()
        conn.close()

        return f"✅ **Ficha de Inimigo salva com sucesso no Banco de Dados Local!**\n" + cls.get_status(name)

    @classmethod
    def generate_health_bar(cls, current_hp: int, max_hp: int) -> str:
        if max_hp <= 0:
            pct = 0
        else:
            pct = max(0, min(100, int((current_hp / max_hp) * 100)))

        total_bars = 50
        filled_bars = int((pct / 100) * total_bars)
        empty_bars = total_bars - filled_bars

        bar_str = "|" * filled_bars + "-" * empty_bars
        return f"~[-{bar_str}-]{pct}%~"

    @classmethod
    def attack(cls, name: str, damage: int) -> str:
        key = name.strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM enemy_sheets WHERE name_lower=?", (key,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"❌ Inimigo **\"{name}\"** não foi encontrado no Banco de Dados!"

        new_hp = max(0, row["current_hp"] - damage)
        new_status = "Deceased" if new_hp == 0 else row["status"]

        cursor.execute("UPDATE enemy_sheets SET current_hp=?, status=? WHERE name_lower=?", (new_hp, new_status, key))
        conn.commit()
        conn.close()

        return f"⚔️ **Ataque em {row['name']} (Dano: {damage}):**\n" + cls.get_status(name)

    @classmethod
    def heal(cls, name: str, amount: int) -> str:
        key = name.strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM enemy_sheets WHERE name_lower=?", (key,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"❌ Inimigo **\"{name}\"** não foi encontrado no Banco de Dados!"

        new_hp = min(row["max_hp"], row["current_hp"] + amount)
        new_status = "Alive" if (new_hp > 0 and row["status"] == "Deceased") else row["status"]

        cursor.execute("UPDATE enemy_sheets SET current_hp=?, status=? WHERE name_lower=?", (new_hp, new_status, key))
        conn.commit()
        conn.close()

        return f"💚 **Cura em {row['name']} (+{amount} HP):**\n" + cls.get_status(name)

    @classmethod
    def set_status(cls, name: str, new_status: str) -> str:
        key = name.strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM enemy_sheets WHERE name_lower=?", (key,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"❌ Inimigo **\"{name}\"** não foi encontrado no Banco de Dados!"

        status_fmt = new_status.strip().capitalize()
        cursor.execute("UPDATE enemy_sheets SET status=? WHERE name_lower=?", (status_fmt, key))
        conn.commit()
        conn.close()

        return f"📌 Status de **{row['name']}** alterado para **{status_fmt}**!\n" + cls.get_status(name)

    @classmethod
    def delete_enemy(cls, name: str) -> str:
        key = name.strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM enemy_sheets WHERE name_lower=?", (key,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return f"❌ Inimigo **\"{name}\"** não foi encontrado no Banco de Dados!"

        cursor.execute("DELETE FROM enemy_sheets WHERE name_lower=?", (key,))
        conn.commit()
        conn.close()

        return f"🗑️ **Ficha de {row['name']} finalizada e removida do Banco de Dados!**"

    @classmethod
    def get_status(cls, name: str) -> str:
        key = name.strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM enemy_sheets WHERE name_lower=?", (key,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return f"❌ Inimigo **\"{name}\"** não foi encontrado no Banco de Dados!"

        health_bar = cls.generate_health_bar(row["current_hp"], row["max_hp"])
        
        return (
            f"```text\n"
            f"{{Enemy Sheet}}{row['name']} AC: {row['ac']}\n"
            f"HP: {row['current_hp']}/{row['max_hp']}\n"
            f"Status: {row['status']}\n"
            f"{health_bar}\n"
            f"```"
        )

    @classmethod
    def get_all_enemies(cls) -> list[dict]:
        """Retorna todas as fichas salvas no SQLite para a interface desktop."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM enemy_sheets ORDER BY name ASC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]


class RPGCog(commands.Cog):
    """Módulo RPG: Motor Rollem & Fichas de Inimigos com SQLite Local."""

    def __init__(self, bot=None):
        self.bot = bot

    @staticmethod
    def _roll_single_dice_token(match):
        raw_token = match.group(0)
        
        # 1. Dados Fate / Fudge (dF ou XdF)
        fudge_match = re.match(r'^(\d*)dF$', raw_token, re.IGNORECASE)
        if fudge_match:
            count = int(fudge_match.group(1)) if fudge_match.group(1) else 1
            count = max(1, min(100, count))
            rolls = [random.choice([-1, 0, 1]) for _ in range(count)]
            total = sum(rolls)
            
            formatted = []
            for r in rolls:
                if r == 1:
                    formatted.append("+1")
                elif r == -1:
                    formatted.append("-1")
                else:
                    formatted.append("0")
            rolls_str = ", ".join(formatted)
            expanded = f"[{rolls_str}] {raw_token}"
            return float(total), expanded, "", False

        # 2. Dados Padrão
        pattern = r'^(\d*)d(\d+)(!(?:\d+)?)?(ns)?(\+\+\d+|\-\-\d+)?(?:(dh|dl|d|kh|kl|k)(\d+))?(?:(<<|>>)(\d+))?$'
        m = re.match(pattern, raw_token, re.IGNORECASE)
        if not m:
            raise ValueError("Token de dado inválido")

        count_str, sides_str, explode_str, ns_str, per_die_mod, keep_drop_op, keep_drop_num, success_op, success_num = m.groups()

        count = int(count_str) if count_str else 1
        sides = int(sides_str)
        count = max(1, min(100, count))
        sides = max(2, min(10000, sides))

        rolls = [random.randint(1, sides) for _ in range(count)]

        # Dados Explosivos
        if explode_str:
            threshold = sides
            if len(explode_str) > 1 and explode_str[1:].isdigit():
                threshold = int(explode_str[1:])
                threshold = max(2, min(sides, threshold))
                
            extra_rolls = []
            for r in list(rolls):
                curr = r
                depth = 0
                while curr >= threshold and depth < 20:
                    depth += 1
                    new_roll = random.randint(1, sides)
                    extra_rolls.append(new_roll)
                    curr = new_roll
            rolls.extend(extra_rolls)

        # Modificador por Dado (++val ou --val)
        if per_die_mod:
            mod_op = per_die_mod[:2]
            mod_val = int(per_die_mod[2:])
            if mod_op == '++':
                rolls = [r + mod_val for r in rolls]
            elif mod_op == '--':
                rolls = [r - mod_val for r in rolls]

        # Keep / Drop
        total_count = len(rolls)
        kept_indices = set(range(total_count))

        if keep_drop_op and keep_drop_num:
            k_num = int(keep_drop_num)
            k_num = max(1, min(total_count, k_num))
            kd_op = keep_drop_op.lower()
            sorted_indices = sorted(range(total_count), key=lambda i: rolls[i])

            if kd_op in ['d', 'dl']:
                kept_indices = set(sorted_indices[k_num:])
            elif kd_op == 'dh':
                kept_indices = set(sorted_indices[:-k_num])
            elif kd_op in ['k', 'kh']:
                kept_indices = set(sorted_indices[-k_num:])
            elif kd_op == 'kl':
                kept_indices = set(sorted_indices[:k_num])

        # Contagem de Sucessos (<< ou >>)
        success_count = None
        if success_op and success_num:
            target_val = int(success_num)
            if success_op == '<<':
                success_count = sum(1 for i in kept_indices if rolls[i] <= target_val)
            elif success_op == '>>':
                success_count = sum(1 for i in kept_indices if rolls[i] >= target_val)

        # Formatação visual
        formatted_rolls = []
        is_crit = False
        is_fumble = False

        for i, val in enumerate(rolls):
            is_max = (val == sides)
            is_min = (val == 1)
            if is_max and count == 1 and not per_die_mod:
                is_crit = True
            if is_min and count == 1 and not per_die_mod:
                is_fumble = True

            val_str = f"**{val}**" if (is_max or is_min) else f"{val}"
            if i in kept_indices:
                formatted_rolls.append(val_str)
            else:
                formatted_rolls.append(f"~~{val_str}~~")

        rolls_str = ", ".join(formatted_rolls)
        
        if success_count is not None:
            expanded = f"[{rolls_str}] {raw_token}"
            return float(success_count), expanded, "", True

        kept_sum = sum(rolls[i] for i in kept_indices)
        expanded = f"[{rolls_str}] {raw_token}"
        
        crit_tag = ""
        if is_crit:
            crit_tag = " **CRÍTICO!**"
        elif is_fumble:
            crit_tag = " **DESASTRE!**"

        return float(kept_sum), expanded, crit_tag, False

    @staticmethod
    def parse_and_roll_dice(text: str) -> tuple[list, int]:
        text_clean = text.strip()
        
        text_clean = re.sub(r'\badv(?:\s+d?20)?\b', '2d20k1', text_clean, flags=re.IGNORECASE)
        text_clean = re.sub(r'\bdis(?:\s+d?20)?\b', '2d20kl1', text_clean, flags=re.IGNORECASE)

        repeat_pattern = r'^(?:\b|^)(\d+)#\s*(.*)'
        repeat_match = re.match(repeat_pattern, text_clean, re.IGNORECASE)

        repeat_count = 1
        target_text = text_clean

        if repeat_match:
            repeat_count = int(repeat_match.group(1))
            repeat_count = max(1, min(20, repeat_count))
            target_text = repeat_match.group(2).strip()

        dice_pattern = r'(\d*)d(\d+|F)(!(?:\d+)?)?(ns)?(\+\+\d+|\-\-\d+)?(?:(dh|dl|d|kh|kl|k)(\d+))?(?:(<<|>>)(\d+))?'
        m_first = re.search(dice_pattern, target_text, re.IGNORECASE)

        if not m_first:
            return [], 0

        # Regra do Prefixo Absoluto: O comando deve estar no início da mensagem!
        first_char_idx = m_first.start()
        prefix_text = target_text[:first_char_idx].strip(' ()+-*/')
        if prefix_text != "":
            return [], 0

        all_matches = list(re.finditer(dice_pattern, target_text, re.IGNORECASE))
        last_match = all_matches[-1]
        
        after_text = target_text[last_match.end():]
        math_tail_m = re.match(r'^(\s*[\+\-\*\/]\s*\d+|\s*\))+\s*', after_text)
        if math_tail_m:
            end_idx = last_match.end() + math_tail_m.end()
        else:
            end_idx = last_match.end()

        pure_math_expr = target_text[:end_idx].strip()
        raw_comment = target_text[end_idx:].strip()
        comment_str = f' "{raw_comment[:20]}"' if raw_comment else ""

        results = []

        for rep in range(1, repeat_count + 1):
            eval_expr = pure_math_expr
            display_expr = pure_math_expr
            
            matches_cur = list(re.finditer(dice_pattern, pure_math_expr, re.IGNORECASE))
            if not matches_cur:
                break

            overall_crit_tag = ""
            is_success_mode = False

            for m in reversed(matches_cur):
                try:
                    val, expanded, crit_tag, is_succ = RPGCog._roll_single_dice_token(m)
                    if is_succ:
                        is_success_mode = True
                    if crit_tag and not overall_crit_tag:
                        overall_crit_tag = crit_tag
                    
                    start_idx, end_idx_m = m.span()
                    eval_expr = eval_expr[:start_idx] + str(val) + eval_expr[end_idx_m:]
                    display_expr = display_expr[:start_idx] + expanded + display_expr[end_idx_m:]
                except Exception:
                    return [], 0

            try:
                total_val = evaluate_math_string(eval_expr)
            except Exception:
                total_val = 0.0

            display_total = int(total_val) if total_val.is_integer() else round(total_val, 2)

            display_formatted = re.sub(r'(?<!\+)(?<!\-)([(\)*\/]|\+(?!\+)|\-(?!\-))', r' \1 ', display_expr)
            display_formatted = re.sub(r'\s+', ' ', display_formatted).strip()

            prefix = f"`{rep}#` " if repeat_count > 1 else ""
            
            if is_success_mode:
                line = f"{prefix}**{display_total}** sucessos  ⟵ {display_formatted}{comment_str}"
            else:
                line = f"{prefix}**{display_total}**  ⟵ {display_formatted}{overall_crit_tag}{comment_str}"
                
            results.append(line)

        return results, repeat_count

    @commands.command(name="set_enemy", aliases=["newenemy", "setenemy"])
    async def set_enemy_cmd(self, ctx, *, text: str = None):
        """Cria ou atualiza uma ficha de inimigo no SQLite. Uso: !set {Enemy Sheet}Name: "Nome"; HP: 50; AC: 15;"""
        if not text:
            await ctx.send(EnemyManager.get_template())
            return
        res = EnemyManager.create_or_update_enemy(text, str(ctx.guild.id if ctx.guild else 'global'))
        await ctx.send(res)

    @commands.command(name="atk")
    async def atk_cmd(self, ctx, name: str, damage: int):
        """Causa dano a um inimigo. Uso: !atk "Nome" X"""
        res = EnemyManager.attack(name, damage)
        await ctx.send(res)

    @commands.command(name="heal")
    async def heal_cmd(self, ctx, name: str, amount: int):
        """Cura um inimigo. Uso: !heal "Nome" X"""
        res = EnemyManager.heal(name, amount)
        await ctx.send(res)

    @commands.command(name="status")
    async def status_cmd(self, ctx, name: str):
        """Exibe o status de um inimigo. Uso: !status "Nome" """
        res = EnemyManager.get_status(name)
        await ctx.send(res)

    @commands.command(name="delete_enemy", aliases=["deleteenemy", "delenemy"])
    async def delete_enemy_cmd(self, ctx, name: str):
        """Remove a ficha de um inimigo. Uso: !delete "Nome" """
        res = EnemyManager.delete_enemy(name)
        await ctx.send(res)

    @staticmethod
    def coin_flip() -> str:
        return random.choice(["Cara", "Coroa"])

async def setup(bot):
    await bot.add_cog(RPGCog(bot))
