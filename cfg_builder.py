"""Construa um CFG auxiliar por função, preservando os nós da AST."""

from __future__ import annotations

import load_previous  # Disponibiliza os módulos das etapas anteriores.

from ast_nodes import Block, FunctionDecl, IfStmt, Stmt, WhileStmt, ReturnStmt, BoolLiteral
from cfg import BlockId, CFG, Jump, ScopeExit, Return, Branch


class CFGBuilder:
    def build(self, function: FunctionDecl) -> CFG:
        self.cfg = CFG(function)
        body_entry = self.cfg.new_block()
        self.cfg.terminate(self.cfg.entry, Jump(body_entry.id))
        continuation = self._build_block(function.body, body_entry.id)
        if continuation is not None:
            self.cfg.terminate(continuation, Jump(self.cfg.fallthrough_exit))
        return self.cfg

    def _build_block(self, block: Block, current: BlockId) -> BlockId | None:
        """Percorra um bloco da AST e devolva sua continuação normal.

        `current` identifica um bloco básico aberto. Comandos sequenciais
        permanecem nele. Comandos de controle podem mudar a continuação.
        None indica que os caminhos deste bloco não alcançam o próximo comando.
        """

        for s in block.statements:
            if current is None:
                break

            current = self._build_statement(s, current)

        # Sinalizar fim de bloco
        if current is not None:
            self.cfg.blocks[current].operations.append(ScopeExit(block.metadata["scope"]))
            
        return current

    def _build_statement(self, statement: Stmt, current: BlockId) -> BlockId | None:

        if isinstance(statement, Block):
            return self._build_block(statement, current)

        elif isinstance(statement, IfStmt):
            return self._build_if(statement, current)

        elif isinstance(statement, WhileStmt):
            return self._build_while(statement, current)

        # adiciona a operação e termina o bloco
        elif isinstance(statement, ReturnStmt):
            # não adicionamos em operations
            self.cfg.terminate(current, Return(statement))
            
            # sem bloco seguinte, retornamos None
            return None

        # outros comandos só são adicionados ao bloco atual de CFG
        else:
            self.cfg.blocks[current].operations.append(statement)
            return current

    def _build_if(self, statement: IfStmt, current: BlockId) -> BlockId | None:

        then_blk = self.cfg.new_block()
        if statement.else_block:
            else_blk = self.cfg.new_block()
        next_blk = self.cfg.new_block()


        if statement.else_block:
            self.cfg.terminate(current, Branch(statement.condition, then_blk.id, else_blk.id))
        else:
            self.cfg.terminate(current, Branch(statement.condition, then_blk.id, next_blk.id))


        # se os blocos then e else não retornam None, quer dizer que após sua execução, continuam pelo código seguinte
        curr_then = self._build_block(statement.then_block, then_blk.id)
        if curr_then is not None:
            self.cfg.terminate(curr_then, Jump(next_blk.id))

        if statement.else_block:
            curr_else = self._build_block(statement.else_block, else_blk.id)
            if curr_else is not None:
                self.cfg.terminate(curr_else, Jump(next_blk.id))

        # devemos retornar None se nenhum caminho continua após o if.
        if statement.else_block and curr_then is None and curr_else is None:
            return None

        return next_blk.id

    def _build_while(self, statement: WhileStmt, current: BlockId) -> BlockId | None:

        # teste precisa ser um bloco para voltarmos a ele toda vez que a iteração do loop acaba
        test_blk = self.cfg.new_block()
        body_blk = self.cfg.new_block()
        next_blk = self.cfg.new_block()


        # do bloco anterior para o bloco de teste, no teste a condição é avaliada
        self.cfg.terminate(current, Jump(test_blk.id))
        self.cfg.terminate(test_blk.id, Branch(statement.condition, body_blk.id, next_blk.id))


        curr_body = self._build_block(statement.body, body_blk.id)

        if curr_body is not None:
            self.cfg.terminate(curr_body, Jump(test_blk.id))


        # loop infinito
        if isinstance(statement.condition, BoolLiteral) and statement.condition.value is True:
            return None

        # loops finitos
        return next_blk.id
